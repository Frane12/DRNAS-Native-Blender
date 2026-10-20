#define VK_USE_PLATFORM_ANDROID_KHR
#include <vulkan/vulkan.h>
#include <android/native_window_jni.h>
#include "ghost_input_bridge.h"
#include <time.h>
#include <jni.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
 * Phase 1 graphics validation: actual Android Vulkan surface, swapchain,
 * single clear-and-present frame. Input is queued for a future Android GHOST backend.
 * This is NOT Blender GPU/GHOST rendering.
 * The native input bridge captures actions; GHOST integration is phase 2.
 */
JNIEXPORT void JNICALL
Java_hr_drnas_nativeprobe_MainActivity_nativeInput(
    JNIEnv *env, jobject activity, jint action, jfloat x, jfloat y, jfloat value)
{
    (void)env; (void)activity;
    struct timespec now = {0};
    clock_gettime(CLOCK_MONOTONIC, &now);
    uint64_t ns = ((uint64_t) now.tv_sec * 1000000000ULL) + (uint64_t) now.tv_nsec;
    drnas_input_enqueue(action, x, y, value, ns);
}

static int supports_extension(const VkExtensionProperties *list,
                              uint32_t count, const char *name)
{
    for (uint32_t i = 0; i < count; i++)
        if (strcmp(list[i].extensionName, name) == 0) return 1;
    return 0;
}

JNIEXPORT jstring JNICALL
Java_hr_drnas_nativeprobe_MainActivity_nativeVulkanDraw(
    JNIEnv *env, jobject activity, jobject java_surface)
{
    (void)activity;
    char msg[1024] = {0};
    const char *stage = "native initialization";
    VkResult code = VK_SUCCESS;
    ANativeWindow *window = NULL;
    VkInstance instance = VK_NULL_HANDLE;
    VkSurfaceKHR surface = VK_NULL_HANDLE;
    VkDevice device = VK_NULL_HANDLE;
    VkSwapchainKHR swapchain = VK_NULL_HANDLE;
    VkRenderPass renderpass = VK_NULL_HANDLE;
    VkCommandPool commandpool = VK_NULL_HANDLE;
    VkSemaphore acquired = VK_NULL_HANDLE, rendered = VK_NULL_HANDLE;
    VkFence fence = VK_NULL_HANDLE;
    VkFramebuffer *fb = NULL;
    VkImageView *views = NULL;
    VkImage *images = NULL;
    uint32_t image_count = 0;
    VkPhysicalDevice physical = VK_NULL_HANDLE;
    VkQueue queue = VK_NULL_HANDLE;
    uint32_t family = UINT32_MAX;
    const char *gpu_name = "(none)";
    uint32_t vk_version = 0;

    if (!java_surface) {
        snprintf(msg, sizeof(msg), "Vulkan FAIL: no Java surface.");
        goto cleanup;
    }
    window = ANativeWindow_fromSurface(env, java_surface);
    if (!window) {
        snprintf(msg, sizeof(msg), "Vulkan FAIL: ANativeWindow_fromSurface.");
        goto cleanup;
    }

#define VK_TRY(what, expr) do { \
    stage = (what); code = (expr); \
    if (code != VK_SUCCESS) goto failed; \
} while (0)

    /* Instance: Android Vulkan WSI, no desktop X11/Wayland extension. */
    const char *inst_ext[] = {
        VK_KHR_SURFACE_EXTENSION_NAME, VK_KHR_ANDROID_SURFACE_EXTENSION_NAME
    };
    VkApplicationInfo app = { .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO };
    app.pApplicationName = "DRNAS Native Vulkan LAB";
    app.apiVersion = VK_API_VERSION_1_0;
    VkInstanceCreateInfo ici = { .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO };
    ici.pApplicationInfo = &app;
    ici.enabledExtensionCount = 2;
    ici.ppEnabledExtensionNames = inst_ext;
    VK_TRY("vkCreateInstance", vkCreateInstance(&ici, NULL, &instance));

    VkAndroidSurfaceCreateInfoKHR asc = {
        .sType = VK_STRUCTURE_TYPE_ANDROID_SURFACE_CREATE_INFO_KHR,
        .window = window
    };
    VK_TRY("vkCreateAndroidSurfaceKHR",
           vkCreateAndroidSurfaceKHR(instance, &asc, NULL, &surface));

    uint32_t device_count = 0;
    VK_TRY("vkEnumeratePhysicalDevices(count)",
           vkEnumeratePhysicalDevices(instance, &device_count, NULL));
    if (!device_count) {
        snprintf(msg, sizeof(msg), "Vulkan FAIL: Android driver has no GPU device.");
        goto cleanup;
    }
    VkPhysicalDevice *devices = calloc(device_count, sizeof(*devices));
    if (!devices) goto oom;
    code = vkEnumeratePhysicalDevices(instance, &device_count, devices);
    if (code != VK_SUCCESS) {
        free(devices); stage = "vkEnumeratePhysicalDevices(data)"; goto failed;
    }
    for (uint32_t d = 0; d < device_count && family == UINT32_MAX; d++) {
        uint32_t n = 0;
        vkGetPhysicalDeviceQueueFamilyProperties(devices[d], &n, NULL);
        VkQueueFamilyProperties *qs = calloc(n, sizeof(*qs));
        if (!qs) continue;
        vkGetPhysicalDeviceQueueFamilyProperties(devices[d], &n, qs);
        for (uint32_t q = 0; q < n; q++) {
            VkBool32 can_present = VK_FALSE;
            if ((qs[q].queueFlags & VK_QUEUE_GRAPHICS_BIT) &&
                vkGetPhysicalDeviceSurfaceSupportKHR(devices[d], q, surface,
                                                    &can_present) == VK_SUCCESS &&
                can_present) {
                physical = devices[d];
                family = q;
                break;
            }
        }
        free(qs);
    }
    free(devices);
    if (family == UINT32_MAX) {
        snprintf(msg, sizeof(msg), "Vulkan FAIL: No Android graphics+present queue.");
        goto cleanup;
    }
    VkPhysicalDeviceProperties props;
    vkGetPhysicalDeviceProperties(physical, &props);
    vk_version = props.apiVersion;

    uint32_t device_ext_count = 0;
    VK_TRY("vkEnumerateDeviceExtensionProperties(count)",
           vkEnumerateDeviceExtensionProperties(physical, NULL, &device_ext_count, NULL));
    VkExtensionProperties *device_ext = calloc(device_ext_count, sizeof(*device_ext));
    if (!device_ext) goto oom;
    code = vkEnumerateDeviceExtensionProperties(physical, NULL, &device_ext_count, device_ext);
    int swapchain_supported =
        (code == VK_SUCCESS &&
         supports_extension(device_ext, device_ext_count, VK_KHR_SWAPCHAIN_EXTENSION_NAME));
    free(device_ext);
    if (!swapchain_supported) {
        snprintf(msg, sizeof(msg), "Vulkan FAIL: VK_KHR_swapchain unavailable.");
        goto cleanup;
    }

    float priority = 1.0f;
    VkDeviceQueueCreateInfo qci = {
        .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
        .queueFamilyIndex = family, .queueCount = 1, .pQueuePriorities = &priority
    };
    const char *extensions[] = { VK_KHR_SWAPCHAIN_EXTENSION_NAME };
    VkDeviceCreateInfo dci = {
        .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
        .queueCreateInfoCount = 1, .pQueueCreateInfos = &qci,
        .enabledExtensionCount = 1, .ppEnabledExtensionNames = extensions
    };
    VK_TRY("vkCreateDevice", vkCreateDevice(physical, &dci, NULL, &device));
    vkGetDeviceQueue(device, family, 0, &queue);

    VkSurfaceCapabilitiesKHR caps;
    VK_TRY("vkGetPhysicalDeviceSurfaceCapabilitiesKHR",
           vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical, surface, &caps));
    if (!(caps.supportedUsageFlags & VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT)) {
        snprintf(msg, sizeof(msg), "Vulkan FAIL: no color-attachment swapchain usage.");
        goto cleanup;
    }
    uint32_t nf = 0;
    VK_TRY("vkGetPhysicalDeviceSurfaceFormatsKHR(count)",
           vkGetPhysicalDeviceSurfaceFormatsKHR(physical, surface, &nf, NULL));
    if (!nf) { snprintf(msg, sizeof(msg), "Vulkan FAIL: no surface formats."); goto cleanup; }
    VkSurfaceFormatKHR *formats = calloc(nf, sizeof(*formats));
    if (!formats) goto oom;
    code = vkGetPhysicalDeviceSurfaceFormatsKHR(physical, surface, &nf, formats);
    if (code != VK_SUCCESS) { free(formats); stage = "surface formats"; goto failed; }
    VkSurfaceFormatKHR chosen = formats[0];
    if (chosen.format == VK_FORMAT_UNDEFINED) {
        chosen.format = VK_FORMAT_R8G8B8A8_UNORM;
        chosen.colorSpace = VK_COLOR_SPACE_SRGB_NONLINEAR_KHR;
    } else {
        for (uint32_t i = 0; i < nf; i++)
            if (formats[i].format == VK_FORMAT_R8G8B8A8_UNORM ||
                formats[i].format == VK_FORMAT_B8G8R8A8_UNORM) {
                chosen = formats[i]; break;
            }
    }
    free(formats);
    VkExtent2D extent = caps.currentExtent;
    if (extent.width == UINT32_MAX) {
        uint32_t w = (uint32_t)ANativeWindow_getWidth(window);
        uint32_t h = (uint32_t)ANativeWindow_getHeight(window);
        extent.width = w < caps.minImageExtent.width ? caps.minImageExtent.width : w;
        extent.height = h < caps.minImageExtent.height ? caps.minImageExtent.height : h;
        if (extent.width > caps.maxImageExtent.width) extent.width = caps.maxImageExtent.width;
        if (extent.height > caps.maxImageExtent.height) extent.height = caps.maxImageExtent.height;
    }
    if (!extent.width || !extent.height) {
        snprintf(msg, sizeof(msg), "Vulkan FAIL: zero-size Android surface.");
        goto cleanup;
    }
    uint32_t requested_images = caps.minImageCount + 1;
    if (caps.maxImageCount && requested_images > caps.maxImageCount)
        requested_images = caps.maxImageCount;
    VkCompositeAlphaFlagBitsKHR alpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
    if (!(caps.supportedCompositeAlpha & alpha)) {
        const VkCompositeAlphaFlagBitsKHR opts[] = {
            VK_COMPOSITE_ALPHA_PRE_MULTIPLIED_BIT_KHR,
            VK_COMPOSITE_ALPHA_POST_MULTIPLIED_BIT_KHR,
            VK_COMPOSITE_ALPHA_INHERIT_BIT_KHR
        };
        for (int i = 0; i < 3; i++)
            if (caps.supportedCompositeAlpha & opts[i]) { alpha = opts[i]; break; }
    }
    VkSwapchainCreateInfoKHR sci = {
        .sType = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR,
        .surface = surface, .minImageCount = requested_images,
        .imageFormat = chosen.format, .imageColorSpace = chosen.colorSpace,
        .imageExtent = extent, .imageArrayLayers = 1,
        .imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
        .imageSharingMode = VK_SHARING_MODE_EXCLUSIVE,
        .preTransform = caps.currentTransform, .compositeAlpha = alpha,
        .presentMode = VK_PRESENT_MODE_FIFO_KHR, .clipped = VK_TRUE
    };
    VK_TRY("vkCreateSwapchainKHR", vkCreateSwapchainKHR(device, &sci, NULL, &swapchain));
    VK_TRY("vkGetSwapchainImagesKHR(count)",
           vkGetSwapchainImagesKHR(device, swapchain, &image_count, NULL));
    if (!image_count) { snprintf(msg, sizeof(msg), "Vulkan FAIL: empty swapchain."); goto cleanup; }
    images = calloc(image_count, sizeof(*images));
    views = calloc(image_count, sizeof(*views));
    fb = calloc(image_count, sizeof(*fb));
    if (!images || !views || !fb) goto oom;
    VK_TRY("vkGetSwapchainImagesKHR(data)",
           vkGetSwapchainImagesKHR(device, swapchain, &image_count, images));

    VkAttachmentDescription attachment = {
        .format = chosen.format, .samples = VK_SAMPLE_COUNT_1_BIT,
        .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR, .storeOp = VK_ATTACHMENT_STORE_OP_STORE,
        .stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        .stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
        .finalLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR
    };
    VkAttachmentReference ref = {
        .attachment = 0, .layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL
    };
    VkSubpassDescription subpass = {
        .pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS,
        .colorAttachmentCount = 1, .pColorAttachments = &ref
    };
    VkSubpassDependency dep = {
        .srcSubpass = VK_SUBPASS_EXTERNAL, .dstSubpass = 0,
        .srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
        .dstStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
        .dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT
    };
    VkRenderPassCreateInfo rpci = {
        .sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO,
        .attachmentCount = 1, .pAttachments = &attachment,
        .subpassCount = 1, .pSubpasses = &subpass,
        .dependencyCount = 1, .pDependencies = &dep
    };
    VK_TRY("vkCreateRenderPass", vkCreateRenderPass(device, &rpci, NULL, &renderpass));

    for (uint32_t i = 0; i < image_count; i++) {
        VkImageViewCreateInfo iv = {
            .sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
            .image = images[i], .viewType = VK_IMAGE_VIEW_TYPE_2D,
            .format = chosen.format,
            .subresourceRange = {
                .aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
                .baseMipLevel = 0, .levelCount = 1,
                .baseArrayLayer = 0, .layerCount = 1
            }
        };
        VK_TRY("vkCreateImageView", vkCreateImageView(device, &iv, NULL, &views[i]));
        VkFramebufferCreateInfo fci = {
            .sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO,
            .renderPass = renderpass, .attachmentCount = 1,
            .pAttachments = &views[i],
            .width = extent.width, .height = extent.height, .layers = 1
        };
        VK_TRY("vkCreateFramebuffer", vkCreateFramebuffer(device, &fci, NULL, &fb[i]));
    }
    VkCommandPoolCreateInfo cpci = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
        .queueFamilyIndex = family, .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT
    };
    VK_TRY("vkCreateCommandPool", vkCreateCommandPool(device, &cpci, NULL, &commandpool));
    VkCommandBuffer cmd = VK_NULL_HANDLE;
    VkCommandBufferAllocateInfo cai = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
        .commandPool = commandpool, .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
        .commandBufferCount = 1
    };
    VK_TRY("vkAllocateCommandBuffers", vkAllocateCommandBuffers(device, &cai, &cmd));
    VkSemaphoreCreateInfo sem = { .sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO };
    VK_TRY("vkCreateSemaphore(acquired)",
           vkCreateSemaphore(device, &sem, NULL, &acquired));
    VK_TRY("vkCreateSemaphore(rendered)",
           vkCreateSemaphore(device, &sem, NULL, &rendered));
    VkFenceCreateInfo fci = { .sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
    VK_TRY("vkCreateFence", vkCreateFence(device, &fci, NULL, &fence));

    uint32_t idx = 0;
    VK_TRY("vkAcquireNextImageKHR",
           vkAcquireNextImageKHR(device, swapchain, UINT64_MAX, acquired, VK_NULL_HANDLE, &idx));
    VkCommandBufferBeginInfo begin = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
        .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT
    };
    VK_TRY("vkBeginCommandBuffer", vkBeginCommandBuffer(cmd, &begin));
    VkClearValue clear = { .color = {{ 0.035f, 0.12f, 0.20f, 1.0f }} };
    VkRenderPassBeginInfo rpbi = {
        .sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
        .renderPass = renderpass, .framebuffer = fb[idx],
        .renderArea = { .offset = {0, 0}, .extent = extent },
        .clearValueCount = 1, .pClearValues = &clear
    };
    vkCmdBeginRenderPass(cmd, &rpbi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdEndRenderPass(cmd);
    VK_TRY("vkEndCommandBuffer", vkEndCommandBuffer(cmd));
    VkPipelineStageFlags waitstage = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    VkSubmitInfo si = {
        .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
        .waitSemaphoreCount = 1, .pWaitSemaphores = &acquired,
        .pWaitDstStageMask = &waitstage,
        .commandBufferCount = 1, .pCommandBuffers = &cmd,
        .signalSemaphoreCount = 1, .pSignalSemaphores = &rendered
    };
    VK_TRY("vkQueueSubmit", vkQueueSubmit(queue, 1, &si, fence));
    VkPresentInfoKHR pi = {
        .sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR,
        .waitSemaphoreCount = 1, .pWaitSemaphores = &rendered,
        .swapchainCount = 1, .pSwapchains = &swapchain, .pImageIndices = &idx
    };
    VK_TRY("vkQueuePresentKHR", vkQueuePresentKHR(queue, &pi));
    VK_TRY("vkQueueWaitIdle", vkQueueWaitIdle(queue));
    DrnasInputStats input_stats;
    drnas_input_get_stats(&input_stats);
    snprintf(msg, sizeof(msg),
             "VULKAN PASS: real Android frame presented. GPU: %s | API %u.%u | surface %ux%u | queue %u | native input FIFO %llu events (%u pending) | Blender GHOST not connected",
             props.deviceName, VK_VERSION_MAJOR(vk_version), VK_VERSION_MINOR(vk_version),
             extent.width, extent.height, family, (unsigned long long) input_stats.received,
             input_stats.pending);
    goto cleanup;

oom:
    snprintf(msg, sizeof(msg), "Vulkan FAIL: out of memory.");
    goto cleanup;
failed:
    snprintf(msg, sizeof(msg), "Vulkan FAIL: %s -> VkResult %d", stage, (int)code);
cleanup:
    if (device != VK_NULL_HANDLE) {
        vkDeviceWaitIdle(device);
        if (fence) vkDestroyFence(device, fence, NULL);
        if (rendered) vkDestroySemaphore(device, rendered, NULL);
        if (acquired) vkDestroySemaphore(device, acquired, NULL);
        if (commandpool) vkDestroyCommandPool(device, commandpool, NULL);
        if (fb) for (uint32_t i = 0; i < image_count; i++)
            if (fb[i]) vkDestroyFramebuffer(device, fb[i], NULL);
        if (views) for (uint32_t i = 0; i < image_count; i++)
            if (views[i]) vkDestroyImageView(device, views[i], NULL);
        if (renderpass) vkDestroyRenderPass(device, renderpass, NULL);
        if (swapchain) vkDestroySwapchainKHR(device, swapchain, NULL);
        vkDestroyDevice(device, NULL);
    }
    free(fb); free(views); free(images);
    if (surface) vkDestroySurfaceKHR(instance, surface, NULL);
    if (instance) vkDestroyInstance(instance, NULL);
    if (window) ANativeWindow_release(window);
    return (*env)->NewStringUTF(env, msg);
}
