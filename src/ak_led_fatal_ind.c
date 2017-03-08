#include "stm32f1xx_hal.h"
#include "ak_led.h"
#include "ak_led_fatal_ind.h"

#define END {0, 0}

typedef struct {
    uint32_t on_ms;
    uint32_t off_ms;
} pattern_el;

static pattern_el hard_els[] = {{10, 10}, END};

__attribute__((noreturn))
void ak_led_fatal_ind_loop(const ak_led_fatal_pattern pattern) {
    const pattern_el const *pattern_els;

    switch(pattern) {
        case ak_led_fatal_pattern_hard:
            pattern_els = hard_els;
    }

    while(1) {
        pattern_el const *el = pattern_els;
        while(el->on_ms) {
            ak_led_on();
            HAL_Delay(el->on_ms);
            ak_led_off();
            HAL_Delay(el->off_ms);
            el++;
        }
    }
}
