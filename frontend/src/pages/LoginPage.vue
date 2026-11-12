<template>
  <div class="login">
    <section class="login__masthead">
      <div class="login__kicker">三江传媒集团 · 通稿聚合台</div>
      <h1 class="login__title">
        通稿<br />
        聚合台
      </h1>
      <p class="login__desc">
        20 个同行站与 8 个政务号的通稿在这里汇成一条流水线：先按正文密度抽出正文，
        再用 MinHash + LSH 找出同一事件的 6—9 家转载，最后按日给出事件时间轴与日报。
      </p>
      <div class="login__facts">
        <div class="login__fact"><b>60</b><span>抓取原文</span></div>
        <div class="login__fact"><b>48</b><span>抽取正文</span></div>
        <div class="login__fact"><b>12</b><span>去重簇</span></div>
        <div class="login__fact"><b>6</b><span>事件</span></div>
        <div class="login__fact"><b>3</b><span>疑似边</span></div>
      </div>
    </section>

    <section class="login__card">
      <h2>编辑登录</h2>
      <p class="mono" style="color: var(--ink-faint)">Sign in · 稿件池只对内部编辑开放</p>
      <hr class="rule" />
      <form @submit.prevent="submit">
        <div class="field" style="margin-bottom: var(--space-3)">
          <label for="email">邮箱</label>
          <input
            id="email"
            v-model="email"
            type="email"
            autocomplete="username"
            data-testid="login-email"
            placeholder="analyst@dedupwire.io"
          />
        </div>
        <div class="field" style="margin-bottom: var(--space-4)">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            autocomplete="current-password"
            data-testid="login-password"
            placeholder="Demo@2026"
          />
        </div>
        <button class="btn btn--seal seal-button" type="submit" data-testid="login-submit" :disabled="loading">
          {{ loading ? '核验中…' : '进入编辑台' }}
        </button>
        <div v-if="auth.loginError" class="login__error">{{ auth.loginError }}</div>
      </form>
      <div class="login__accounts">
        演示账号 / Demo@2026<br />
        主编 admin@dedupwire.io · 编辑 analyst@dedupwire.io · 只读 viewer@dedupwire.io
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ROLE_HOME } from '../constants/roles'
import type { RoleKey } from '../types'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('analyst@dedupwire.io')
const password = ref('Demo@2026')
const loading = ref(false)

async function submit() {
  loading.value = true
  const ok = await auth.login(email.value.trim(), password.value)
  loading.value = false
  if (!ok) return
  const redirect = route.query.redirect as string | undefined
  const fallback = ROLE_HOME[(auth.user?.role || 'analyst') as RoleKey] || '/sources'
  await router.push(redirect || fallback)
}
</script>
