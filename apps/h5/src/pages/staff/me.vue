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
<template><StaffShell title="我的"><ResourceState :loading="loading" :error="error" @retry="reload"><section v-if="data" class="me-head"><PhotoAvatar v-if="data.photo_url" :src="data.photo_url" :name="data.name" :size="60" /><span v-else class="portrait-frame" aria-label="未设置职业照"><AnonymousPortrait /></span><div class="profile-text"><b>{{ data.name }}</b><span class="role">{{ data.display_title || data.title }}<span v-if="data.dept" class="sep">｜</span>{{ data.dept }}</span><span v-if="data.mobile" class="num phone">{{ data.mobile }}</span></div></section></ResourceState><van-cell-group inset title="账号"><van-cell title="修改密码" is-link @click="password = true"><template #icon><span class="cell-ico ico-plain"><span class="icon i-lucide-lock" aria-hidden="true" /></span></template></van-cell><van-cell title="NFC 分享" label="手机碰一碰与写贴纸；实物卡库存与挂失暂缓" is-link to="/staff/card/share?tab=nfc"><template #icon><span class="cell-ico ico-ai"><span class="icon i-lucide-nfc" aria-hidden="true" /></span></template></van-cell></van-cell-group><van-cell-group inset title="帮助"><van-cell title="添加到手机桌面" label="像 App 一样一点就开，及时看到新线索" is-link @click="install = true"><template #icon><span class="cell-ico ico-primary"><span class="icon i-lucide-smartphone" aria-hidden="true" /></span></template></van-cell><van-cell title="使用帮助" label="名片可分享二维码、海报或链接；AI 回答以人工确认为准"><template #icon><span class="cell-ico ico-plain"><span class="icon i-lucide-circle-help" aria-hidden="true" /></span></template></van-cell></van-cell-group><van-cell-group inset title="关于"><van-cell title="关于数科名片" value="1.0.0" /></van-cell-group><van-button block class="danger-button logout" icon="sign" @click="logout">退出登录</van-button><PasswordSheet v-model="password" /><van-popup v-model:show="install" position="bottom" round closeable><div class="sheet stack"><h2>添加到手机桌面</h2><p v-if="isIOS">使用 Safari 打开，点击底部「分享」，选择「添加到主屏幕」。</p><p v-else>使用系统浏览器打开，点击浏览器菜单，选择「添加到桌面」或「安装应用」。</p><p class="muted">站内消息需要打开应用后查看，请定期查看消息铃铛。</p><van-button type="primary" @click="install = false">知道了</van-button></div></van-popup></StaffShell></template>
<style scoped>
.me-head{display:flex;align-items:center;gap:14px;padding:12px 16px 20px}
.portrait-frame{display:block;width:60px;height:60px;border-radius:var(--r-pill);overflow:hidden;background:var(--c-ink-2);flex-shrink:0}
.profile-text{min-width:0}
.profile-text b{display:block;font-size:var(--fs-lg);color:var(--c-ink)}
.profile-text .role{font-size:var(--fs-sm);color:var(--c-text-3);margin-top:2px;overflow-wrap:anywhere}
.profile-text .role .sep{margin:0 2px;color:var(--c-text-3)}
.profile-text .phone{display:block;margin-top:4px;font-size:var(--fs-sm);color:var(--c-text-3)}
.cell-ico{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;flex:none;margin-right:12px}
.cell-ico .icon{width:18px;height:18px}
.ico-plain{background:var(--c-bg);color:var(--c-ink)}
.ico-ai{background:var(--c-ai-soft);color:var(--c-ai)}
.ico-primary{background:var(--c-primary-soft);color:var(--c-primary)}
.logout{margin-top:var(--sp-5)}
</style>
