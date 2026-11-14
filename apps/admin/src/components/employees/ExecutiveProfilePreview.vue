<!-- 高管名片档案预览：后端契约未发布前仅展示字段说明，不提供保存 -->
<script setup lang="ts">
const reason =
  "等待后端契约（company_id、可空手机号、login_enabled）发布后启用；当前不会保存任何数据";
</script>
<template>
  <div class="exec-preview">
    <el-alert
      type="warning"
      :closable="false"
      title="预览：当前不可保存"
      :description="reason"
    />
    <p class="muted">
      名片档案用于没有手机号、不开通登录的高管名片。契约发布前，以下字段仅说明含义，输入已禁用；现有“新增员工”流程不受影响。
    </p>
    <el-form label-position="top" class="exec-form" @submit.prevent>
      <el-form-item label="所属企业">
        <el-select
          disabled
          placeholder="待组织架构契约提供可选企业"
          aria-label="所属企业"
        />
        <p class="field-help">
          对应 company_id，从后端返回的企业列表中选择，不在前端写死。
        </p>
      </el-form-item>
      <el-form-item label="名片档案">
        <el-input
          disabled
          placeholder="姓名、职务等档案字段待契约确定"
          aria-label="名片档案"
        />
        <p class="field-help">
          手机号可为空；表格中显示“名片档案”，不会展示空值或虚构号码。
        </p>
      </el-form-item>
      <el-form-item label="登录权限">
        <el-switch
          disabled
          :model-value="false"
          inactive-text="未开通登录"
          aria-label="未开通登录"
        />
        <p class="field-help">
          对应 login_enabled=false；未开通登录的档案不提供重置密码等账号操作。
        </p>
      </el-form-item>
      <div class="toolbar exec-actions">
        <el-tooltip :content="reason" placement="top">
          <span><el-button type="primary" disabled>保存档案</el-button></span>
        </el-tooltip>
      </div>
      <p class="muted exec-reason">{{ reason }}</p>
    </el-form>
  </div>
</template>
<style scoped>
.exec-preview {
  display: grid;
  gap: var(--ac-space-3, 12px);
}
.exec-preview p {
  margin: 0;
}
.exec-form {
  max-width: 100%;
}
.field-help {
  width: 100%;
  margin-top: var(--ac-space-1, 4px) !important;
  font-size: 12px;
  line-height: 1.5;
  color: var(--ac-text-muted, var(--el-text-color-secondary));
}
.exec-actions {
  margin-bottom: 0;
}
.exec-reason {
  font-size: 12px;
}
</style>
