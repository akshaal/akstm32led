#include "stm32f1xx_hal.h"

#include "ak_rtos.h"

static void ak_main_task(void *argument);

void ak_create_main_task() {
    ak_task_create("main", ak_main_task, ak_main_task_priority);
}

static void ak_main_task(void *argument) {
    for(;;) {
        for (int i = 0; i < 100; i++) {
            HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_SET);
            ak_task_delay(20);
            HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);
            ak_task_delay(20);
        }

        for (int i = 0; i < 10; i++) {
            HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_SET);
            ak_task_delay(80);
            HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);
            ak_task_delay(80);
        }
    }
}

