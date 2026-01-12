import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

import { authStore } from '../stores/authStore'

import LoginPage from '../pages/LoginPage/LoginPage.vue'
import RegisterPage from '../pages/RegisterPage/RegisterPage.vue'
import ProjectsPage from '../pages/ProjectsPage/ProjectsPage.vue'
import ProjectWorkspacePage from '../pages/ProjectWorkspacePage/ProjectWorkspacePage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterPage,
    meta: { requiresAuth: false }
  },
  {
    path: '/projects',
    name: 'Projects',
    component: ProjectsPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:id',
    name: 'ProjectWorkspace',
    component: ProjectWorkspacePage,
    meta: { requiresAuth: true }
  },
  {
    path: '/',
    redirect: '/projects'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, _from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false
  const isAuthenticated = authStore.isAuthenticated.value

  if (requiresAuth && !isAuthenticated) {
    // Redirect to login if authentication required but user not authenticated
    next('/login')
  } else if (!requiresAuth && isAuthenticated) {
    // Redirect authenticated users away from login/register to projects
    next('/projects')
  } else {
    next()
  }
})

export default router
