#include "../app/src/main/cpp/ghost_input_bridge.h"

#include <assert.h>
#include <stdio.h>

static DrnasInputEvent next(int action, uint32_t buttons)
{
    DrnasInputEvent e;
    assert(drnas_input_poll(&e));
    assert(e.action == action);
    assert(e.buttons == buttons);
    return e;
}

int main(void)
{
    DrnasInputStats s;
    DrnasInputEvent e;

    drnas_input_reset();
    assert(!drnas_input_poll(&e));
    drnas_input_enqueue(0, 0, 0, 0, 0); /* invalid, ignored */
    drnas_input_enqueue(DRNAS_INPUT_MOVE, 10, 20, 0, 100);
    drnas_input_enqueue(DRNAS_INPUT_MOVE, 30, 40, 0, 200);
    drnas_input_get_stats(&s);
    assert(s.received == 2 && s.coalesced_moves == 1 && s.pending == 1);
    e = next(DRNAS_INPUT_MOVE, 0);
    assert(e.x == 30 && e.y == 40 && e.timestamp_ns == 200);

    drnas_input_enqueue(DRNAS_INPUT_LMB_DOWN, 0, 0, 1, 300);
    drnas_input_enqueue(DRNAS_INPUT_MOVE, 31, 41, 0, 400);
    drnas_input_enqueue(DRNAS_INPUT_RMB_DOWN, 0, 0, 1, 500);
    drnas_input_enqueue(DRNAS_INPUT_ZOOM, 0, 0, -1.5f, 600);
    drnas_input_enqueue(DRNAS_INPUT_LMB_UP, 0, 0, 0, 700);
    drnas_input_enqueue(DRNAS_INPUT_RMB_UP, 0, 0, 0, 800);
    next(DRNAS_INPUT_LMB_DOWN, DRNAS_BUTTON_LEFT);
    next(DRNAS_INPUT_MOVE, DRNAS_BUTTON_LEFT);
    next(DRNAS_INPUT_RMB_DOWN, DRNAS_BUTTON_LEFT | DRNAS_BUTTON_RIGHT);
    e = next(DRNAS_INPUT_ZOOM, DRNAS_BUTTON_LEFT | DRNAS_BUTTON_RIGHT);
    assert(e.value == -1.5f);
    next(DRNAS_INPUT_LMB_UP, DRNAS_BUTTON_RIGHT);
    next(DRNAS_INPUT_RMB_UP, 0);
    assert(!drnas_input_poll(&e));

    drnas_input_reset();
    for (int i = 0; i < DRNAS_INPUT_QUEUE_CAPACITY + 12; i++)
        drnas_input_enqueue(DRNAS_INPUT_ZOOM, 0, 0, (float)i, (uint64_t)i);
    drnas_input_get_stats(&s);
    assert(s.pending == DRNAS_INPUT_QUEUE_CAPACITY && s.dropped == 12);
    e = next(DRNAS_INPUT_ZOOM, 0);
    assert(e.value == 12);
    for (int i = 1; i < DRNAS_INPUT_QUEUE_CAPACITY; i++)
        next(DRNAS_INPUT_ZOOM, 0);
    assert(!drnas_input_poll(&e));

    puts("PASS: DRNAS input FIFO, motion coalescing, button state and bounded overflow");
    return 0;
}
