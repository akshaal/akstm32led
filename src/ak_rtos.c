// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#include "FreeRTOS.h"
#include "task.h"
#include "portable.h"

#include "ak_rtos.h"
#include "ak_led_fatal_ind.h"

void *ak_malloc(size_t xSize) {
    void *rc = pvPortMalloc(xSize);
    if (rc == NULL) {
        ak_led_fatal_ind_loop(ak_led_fatal_pattern_malloc);
    }
    return rc;
}

void ak_free(void *pv) {
    vPortFree(pv);
}

ak_task_handle ak_task_create(char const *name, const ak_task_f f, const ak_task_priority prio) {
    TaskHandle_t task_handle;

    if (xTaskCreate(/* function */          f,
                    /* name */              "main",
                    /* stack size */        128,
                    /* argument */          NULL,
                    /* priority */          prio,
                    /* task handle PTR */   &task_handle) != pdPASS) {
        ak_led_fatal_ind_loop(ak_led_fatal_pattern_task_create);
    }

    return task_handle;
}

void ak_task_delay(const uint32_t millisec) {
    const TickType_t ticks = millisec / portTICK_PERIOD_MS;
    vTaskDelay(ticks ? ticks : 1);
}

ak_task_handle ak_queue_create(int items, int item_size) {
    ak_task_handle qh = xQueueCreate(items, item_size);

    if (qh == NULL) {
        ak_led_fatal_ind_loop(ak_led_fatal_pattern_queue_create);
    }

    return qh;
}
