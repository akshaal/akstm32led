#include "FreeRTOS.h"
#include "task.h"

#include "ak_rtos.h"

ak_task_handle ak_task_create(char const *name, const ak_task_f f, const ak_task_priority prio) {
    TaskHandle_t task_handle;

    xTaskCreate(
        /* function */          f,
        /* name */              "main",
        /* stack size */        128,
        /* argument */          NULL,
        /* priority */          prio,
        /* task handle PTR */   &task_handle);

    return task_handle;
}

void ak_task_delay(const uint32_t millisec) {
    const TickType_t ticks = millisec / portTICK_PERIOD_MS;
    vTaskDelay(ticks ? ticks : 1);
}
