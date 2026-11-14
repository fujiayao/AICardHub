import { ref } from "vue";
import { useTask } from "./useTask";
import type { Page } from "@/api/schema";
export function usePage<T>(fetcher: (page: number) => Promise<Page<T>>) {
  const page = ref(1);
  const data = ref<Page<T>>({ items: [], total: 0, page: 1, page_size: 20 });
  const task = useTask();
  async function load(next = page.value) {
    if (task.busy.value) return;
    page.value = next;
    await task.run(async () => {
      data.value = await fetcher(next);
    });
  }
  return { ...task, page, data, load };
}
