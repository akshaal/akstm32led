// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#include "ak_rtos.h"
#include "ak_led.h"

static void ak_main_task(void *argument);

void ak_create_main_task() {
    ak_task_create("main", ak_main_task, ak_main_task_priority);
}

__attribute__((noreturn))
static void ak_main_task(void *argument) {
    for(;;) {
        for (int i = 0; i < 100; i += 20) {
            for (int z = 0; z < 100 / i; i++) {
                ak_led_off();;
                ak_task_delay(i);
                ak_led_on();
                ak_task_delay(i);
            }
        }
    }
}

