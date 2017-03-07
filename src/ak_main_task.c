#include "stm32f1xx_hal.h"

#include "ak_rtos.h"

static void ak_main_task(void *argument);

void ak_create_main_task() {
    ak_task_create("main", ak_main_task, ak_main_task_priority);
}

static void ak_main_task(void *argument) {
    for(;;) {
        for (int i = 0; i < 100; i += 20) {
            for (int z = 0; z < 100 / i; i++) {
                HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_SET);
                ak_task_delay(i);
                HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);
                ak_task_delay(i);
            }
        }
    }
}

