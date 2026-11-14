<!-- 原型: B12 我的 -->
<script setup lang="ts">
import { showConfirmDialog } from 'vant'
import { shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { card as getCard } from '@/api/generated'
import PhotoAvatar from '@/components/common/PhotoAvatar.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import PasswordSheet from '@/components/staff/PasswordSheet.vue'
import StaffShell from '@/components/staff/StaffShell.vue'
import { useResource } from '@/composables/useResource'
import { isIOS } from '@/platform'
import { useAuthStore } from '@/stores/auth'
const { data, loading, error, reload } = useResource(getCard)
const route = useRoute(); const router = useRouter(); const auth = useAuthStore()
const install = shallowRef(route.query.install === '1'); const password = shallowRef(false)
async function logout() { try { await showConfirmDialog({ title: '退出登录', message: '确定退出当前员工账号？' }); auth.signOut(); router.replace('/staff/login') } catch { /* user cancelled */ } }
</script>
<template><StaffShell title="我的"><ResourceState :loading="loading" :error="error" @retry="reload"><section v-if="data" class="panel row"><PhotoAvatar :src="data.photo_url" :name="data.name" :size="64" /><div><h2>{{ data.name }}</h2><p>{{ data.display_title || data.title }} ｜ {{ data.dept }}</p><p class="muted">{{ data.mobile }}</p></div></section></ResourceState><van-cell-group inset><van-cell title="修改密码" is-link @click="password = true" /><van-cell title="NFC 卡" value="实物管理暂未开放" /></van-cell-group><van-cell-group inset><van-cell title="添加到手机桌面" is-link @click="install = true" /><van-cell title="使用帮助" label="名片可分享二维码、海报或链接；AI 回答以人工确认为准" /><van-cell title="关于" value="本地候选版" /></van-cell-group><van-button block class="danger-button" @click="logout">退出登录</van-button><PasswordSheet v-model="password" /><van-popup v-model:show="install" position="bottom" round closeable><div class="sheet stack"><h2>添加到手机桌面</h2><p v-if="isIOS">使用 Safari 打开，点击底部「分享」，选择「添加到主屏幕」。</p><p v-else>使用系统浏览器打开，点击浏览器菜单，选择「添加到桌面」或「安装应用」。</p><p class="muted">站内消息需要打开应用后查看，请定期查看消息铃铛。</p><van-button type="primary" @click="install = false">知道了</van-button></div></van-popup></StaffShell></template>
