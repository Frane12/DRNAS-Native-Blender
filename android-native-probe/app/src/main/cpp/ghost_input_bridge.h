#ifndef DRNAS_GHOST_INPUT_BRIDGE_H
#define DRNAS_GHOST_INPUT_BRIDGE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Thread-safe Android input transport for a future Blender GHOST backend.
 * This deliberately does not claim to implement Blender's GHOST System yet.
 * A GHOST consumer can poll events without JNI calls or blocking the UI.
 */
enum DrnasInputAction {
    DRNAS_INPUT_MOVE = 1,
    DRNAS_INPUT_LMB_DOWN = 2,
    DRNAS_INPUT_LMB_UP = 3,
    DRNAS_INPUT_RMB_DOWN = 4,
    DRNAS_INPUT_RMB_UP = 5,
    DRNAS_INPUT_ZOOM = 6
};

enum {
    DRNAS_BUTTON_LEFT = 1,
    DRNAS_BUTTON_RIGHT = 2,
    DRNAS_INPUT_QUEUE_CAPACITY = 256
};

typedef struct DrnasInputEvent {
    uint64_t timestamp_ns; /* CLOCK_MONOTONIC, non-wall-clock */
    int32_t action;
    float x, y, value;
    uint32_t buttons; /* state AFTER action, usable for recovery after overflow */
} DrnasInputEvent;

typedef struct DrnasInputStats {
    uint64_t received;
    uint64_t coalesced_moves;
    uint64_t dropped;
    uint32_t pending;
    uint32_t buttons;
} DrnasInputStats;

void drnas_input_reset(void);
void drnas_input_enqueue(int action, float x, float y, float value, uint64_t timestamp_ns);
int drnas_input_poll(DrnasInputEvent *output);
void drnas_input_get_stats(DrnasInputStats *output);

#ifdef __cplusplus
}
#endif
#endif
