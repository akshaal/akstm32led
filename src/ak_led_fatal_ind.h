#ifndef __ak_led_fatal_ind_h
#define __ak_led_fatal_ind_h

typedef enum {
    ak_led_fatal_pattern_hard = 0
} ak_led_fatal_pattern;

__attribute__((noreturn))
void ak_led_fatal_ind_loop(const ak_led_fatal_pattern pattern);

#endif
