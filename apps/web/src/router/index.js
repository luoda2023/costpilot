import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/workspace' },
{
	path: '/workspace',
	name: 'Workspace',
	component: () => import('@/views/Workspace.vue'),
	meta: { title: '工作台' },
},
{
	path: '/docgen',
	name: 'DocGen',
	component: () => import('@/views/DocGen.vue'),
	meta: { title: '文档生成' },
},
{
path: '/prices',
name: 'Prices',
component: () => import('@/views/Prices.vue'),
meta: { title: '价格库' },
},
{
path: '/quote',
name: 'Quote',
component: () => import('@/views/Quote.vue'),
meta: { title: '报价生成' },
},
{
path: '/text-gen',
    name: 'TextGen',
    component: () => import('@/views/TextGen.vue'),
    meta: { title: '文本生成' },
  },
{
 path: '/preview',
 name: 'Preview',
 component: () => import('@/views/Preview.vue'),
 meta: { title: '文件预览' },
  },
  {
 path: '/image-gen',
 name: 'ImageGen',
 component: () => import('@/views/ImageGen.vue'),
 meta: { title: '图片生成' },
  },
{
path: '/chat',
name: 'Chat',
component: () => import('@/views/Chat.vue'),
meta: { title: 'AI 助手' },
},
{
path: '/settings',
name: 'Settings',
component: () => import('@/views/Settings.vue'),
meta: { title: '系统设置' },
},
	]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// 切换页面时更新文档标题
router.afterEach((to) => {
  document.title = (to.meta?.title || '工程助手') + ' - 工程助手'
})

export default router
