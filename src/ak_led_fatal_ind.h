// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#ifndef __ak_led_fatal_ind_h
#define __ak_led_fatal_ind_h

typedef enum {
    ak_led_fatal_pattern_hard = 0,
    ak_led_fatal_pattern_memory = 1,
    ak_led_fatal_pattern_bus = 2,
    ak_led_fatal_pattern_usage = 3,
    ak_led_fatal_pattern_control = 4,
    ak_led_fatal_pattern_osc_config = 5,
    ak_led_fatal_pattern_clock_config = 6,
    ak_led_fatal_pattern_task_create = 7,
    ak_led_fatal_pattern_uart_init = 8,
    ak_led_fatal_pattern_queue_create = 9,
    ak_led_fatal_pattern_malloc = 10
} ak_led_fatal_pattern;

__attribute__((noreturn))
void ak_led_fatal_ind_loop(const ak_led_fatal_pattern pattern);

#endif
