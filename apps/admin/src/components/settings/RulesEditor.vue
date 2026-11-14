<script setup lang="ts">
import { shallowRef, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import { useTask } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
const content = shallowRef(""),
  loaded = shallowRef(false);
const { busy, error, run } = useTask();
async function load() {
  await run(async () => {
    content.value = (await api.rules()).content;
    loaded.value = true;
  });
}
async function save() {
  if (!content.value.trim()) {
    ElMessage.warning("请填写回答规则");
    return;
  }
  await run(async () => {
    await api.saveRules(content.value);
    ElMessage.success("回答规则已保存");
  });
}
onMounted(load);
</script>
<template>
  <section class="page">
    <div>
      <h1>回答规则</h1>
      <p class="muted">
        维护公司级口径、禁答话题、敏感词及免责声明。规则由后端统一用于回答。
      </p>
    </div>
    <div class="panel">
      <LoadState :busy="busy" :error="error" @retry="load" /><el-form
        v-if="loaded"
        label-position="top"
        @submit.prevent="save"
        ><el-form-item label="规则内容" required
          ><el-input
            v-model="content"
            type="textarea"
            :rows="20"
            maxlength="30000"
            show-word-limit /></el-form-item
        ><el-button type="primary" native-type="submit" :loading="busy"
          >保存规则</el-button
        ></el-form
      >
    </div>
  </section>
</template>
