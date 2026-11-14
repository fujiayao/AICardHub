import { shallowRef } from "vue";
import { ElMessageBox } from "element-plus";
export function useTask() {
  const busy = shallowRef(false);
  const error = shallowRef("");
  async function run<T>(task: () => Promise<T>): Promise<T | undefined> {
    if (busy.value) return;
    busy.value = true;
    error.value = "";
    try {
      return await task();
    } catch (e) {
      error.value = e instanceof Error ? e.message : "操作未完成，请重试";
      return undefined;
    } finally {
      busy.value = false;
    }
  }
  return { busy, error, run };
}
export async function confirmAction(message: string) {
  try {
    await ElMessageBox.confirm(message, "确认操作", {
      type: "warning",
      confirmButtonText: "确认",
      cancelButtonText: "取消",
    });
    return true;
  } catch {
    return false;
  }
}
