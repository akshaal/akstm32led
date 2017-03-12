// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#include "stm32f1xx_hal.h"
#include "ak_led.h"
#include "ak_led_fatal_ind.h"

#define END {0, 0}

typedef struct {
    uint32_t on_ms;
    uint32_t off_ms;
} pattern_el;

static const pattern_el const hard_els[] = {{20, 20}, END};
static const pattern_el const memory_els[] = {{500, 500}, END};
static const pattern_el const bus_els[] = {{2000, 2000}, END};
static const pattern_el const usage_els[] = {{2000, 200}, END};
static const pattern_el const control_els[] = {{200, 2000}, END};
static const pattern_el const osc_config_els[] = {{20, 20}, {20, 20}, {20, 20}, {20, 20}, {20, 2000}, END};
static const pattern_el const clock_config_els[] = {{500, 500}, {500, 2000}, END};
static const pattern_el const task_create_els[] = {{500, 500}, {500, 500}, {500, 2000}, END};
static const pattern_el const uart_init_els[] = {{500, 500}, {500, 500}, {500, 500}, {500, 2000}, END};
static const pattern_el const queue_create_els[] = {{500, 500}, {500, 500}, {500, 500}, {500, 500}, {500, 2000}, END};
static const pattern_el const malloc_els[] = {{500, 500}, {500, 500}, {500, 500}, {500, 500}, {500, 500}, {500, 2000}, END};

__attribute__((noreturn))
void ak_led_fatal_ind_loop(const ak_led_fatal_pattern pattern) {
    const pattern_el const *pattern_els;

    switch(pattern) {
    case ak_led_fatal_pattern_hard: pattern_els = hard_els; break;
    case ak_led_fatal_pattern_memory: pattern_els = memory_els; break;
    case ak_led_fatal_pattern_bus: pattern_els = bus_els; break;
    case ak_led_fatal_pattern_usage: pattern_els = usage_els; break;
    case ak_led_fatal_pattern_control: pattern_els = control_els; break;
    case ak_led_fatal_pattern_osc_config: pattern_els = osc_config_els; break;
    case ak_led_fatal_pattern_clock_config: pattern_els = clock_config_els; break;
    case ak_led_fatal_pattern_task_create: pattern_els = task_create_els; break;
    case ak_led_fatal_pattern_uart_init: pattern_els = uart_init_els; break;
    case ak_led_fatal_pattern_queue_create: pattern_els = queue_create_els; break;
    case ak_led_fatal_pattern_malloc: pattern_els = malloc_els; break;
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
