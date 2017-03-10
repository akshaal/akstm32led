// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#include "stm32f1xx_hal.h"
#include "ak_led.h"
#include "ak_led_fatal_ind.h"

#define END {0, 0}

typedef struct {
    uint32_t on_ms;
    uint32_t off_ms;
} pattern_el;

static pattern_el hard_els[] = {{20, 20}, END};
static pattern_el memory_els[] = {{500, 500}, END};
static pattern_el bus_els[] = {{2000, 2000}, END};
static pattern_el usage_els[] = {{2000, 200}, END};
static pattern_el control_els[] = {{200, 2000}, END};
static pattern_el osc_config_els[] = {{20, 20}, {20, 20}, {20, 20}, {20, 20}, {20, 2000}, END};
static pattern_el clock_config_els[] = {{500, 500}, {500, 2000}, END};
static pattern_el task_create_els[] = {{500, 500}, {500, 500}, {500, 2000}, END};
static pattern_el uart_init_els[] = {{500, 500}, {500, 500}, {500, 500}, {500, 2000}, END};
static pattern_el queue_create_els[] = {{500, 500}, {500, 500}, {500, 500}, {500, 500}, {500, 2000}, END};
static pattern_el malloc_els[] = {{500, 500}, {500, 500}, {500, 500}, {500, 500}, {500, 500}, {500, 2000}, END};

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
