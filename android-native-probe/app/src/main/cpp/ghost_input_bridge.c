#include "ghost_input_bridge.h"

#include <pthread.h>
#include <string.h>

/*
 * All operations are O(1), guarded by a short mutex. No malloc, no JNI,
 * no disk/network I/O and no GHOST calls on Android's input/UI thread.
 */
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static DrnasInputEvent events[DRNAS_INPUT_QUEUE_CAPACITY];
static unsigned head, pending;
static uint32_t buttons;
static uint64_t received, coalesced_moves, dropped;

void drnas_input_reset(void)
{
    pthread_mutex_lock(&lock);
    head = pending = buttons = 0;
    received = coalesced_moves = dropped = 0;
    memset(events, 0, sizeof(events));
    pthread_mutex_unlock(&lock);
}

void drnas_input_enqueue(int action, float x, float y, float value, uint64_t timestamp_ns)
{
    if (action < DRNAS_INPUT_MOVE || action > DRNAS_INPUT_ZOOM)
        return;

    pthread_mutex_lock(&lock);
    received++;
    if (action == DRNAS_INPUT_LMB_DOWN) buttons |= DRNAS_BUTTON_LEFT;
    if (action == DRNAS_INPUT_LMB_UP) buttons &= ~DRNAS_BUTTON_LEFT;
    if (action == DRNAS_INPUT_RMB_DOWN) buttons |= DRNAS_BUTTON_RIGHT;
    if (action == DRNAS_INPUT_RMB_UP) buttons &= ~DRNAS_BUTTON_RIGHT;

    DrnasInputEvent event = {
        .timestamp_ns = timestamp_ns, .action = action,
        .x = x, .y = y, .value = value, .buttons = buttons
    };

    /* Only coalesce adjacent pointer motion with the same button state. */
    if (action == DRNAS_INPUT_MOVE && pending) {
        unsigned last = (head + pending - 1) % DRNAS_INPUT_QUEUE_CAPACITY;
        if (events[last].action == DRNAS_INPUT_MOVE &&
            events[last].buttons == buttons) {
            events[last] = event;
            coalesced_moves++;
            pthread_mutex_unlock(&lock);
            return;
        }
    }

    if (pending == DRNAS_INPUT_QUEUE_CAPACITY) {
        /* Oldest event is discarded; latest buttons remain queryable. */
        head = (head + 1) % DRNAS_INPUT_QUEUE_CAPACITY;
        pending--;
        dropped++;
    }
    events[(head + pending) % DRNAS_INPUT_QUEUE_CAPACITY] = event;
    pending++;
    pthread_mutex_unlock(&lock);
}

int drnas_input_poll(DrnasInputEvent *output)
{
    if (!output) return 0;
    pthread_mutex_lock(&lock);
    if (!pending) {
        pthread_mutex_unlock(&lock);
        return 0;
    }
    *output = events[head];
    head = (head + 1) % DRNAS_INPUT_QUEUE_CAPACITY;
    pending--;
    pthread_mutex_unlock(&lock);
    return 1;
}

void drnas_input_get_stats(DrnasInputStats *output)
{
    if (!output) return;
    pthread_mutex_lock(&lock);
    *output = (DrnasInputStats) {
        .received = received, .coalesced_moves = coalesced_moves,
        .dropped = dropped, .pending = pending, .buttons = buttons
    };
    pthread_mutex_unlock(&lock);
}
