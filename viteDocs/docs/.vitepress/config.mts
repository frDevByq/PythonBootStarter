import { defineConfig } from 'vitepress'

const zhSidebar = [
  { text: '开始使用', items: [{ text: '概览', link: '/zh/index.html' }] },
  { text: 'Redis Starter', items: [
    { text: '客户端、工具与分布式锁', link: '/zh/redis.html' },
  ] },
  { text: 'SQLAlchemy Starter', items: [
    { text: '配置、Session 与显式提交', link: '/zh/sqlalchemy.html' },
    { text: '分页查询', link: '/zh/sqlalchemy.html#分页查询' },
  ] },
  { text: 'Web Starter', items: [
    { text: '安装与模块拆分', link: '/zh/web-starter.html' },
    { text: '应用与扫描', link: '/zh/application.html' },
    { text: '路由、异常与上下文', link: '/zh/web.html' },
    { text: 'Web API 参数', link: '/zh/api-reference.html' },
  ] },
]

const enSidebar = [
  { text: 'Getting started', items: [{ text: 'Overview', link: '/en/index.html' }] },
  { text: 'Redis Starter', items: [
    { text: 'Clients, utilities and distributed locks', link: '/en/redis.html' },
  ] },
  { text: 'SQLAlchemy Starter', items: [
    { text: 'Configuration, Sessions and explicit commits', link: '/en/sqlalchemy.html' },
    { text: 'Pagination', link: '/en/sqlalchemy.html#pagination' },
  ] },
  { text: 'Web Starter', items: [
    { text: 'Installation and modules', link: '/en/web-starter.html' },
    { text: 'Application and scanning', link: '/en/application.html' },
    { text: 'Routes, errors and context', link: '/en/web.html' },
    { text: 'Web API parameters', link: '/en/api-reference.html' },
  ] },
]

export default defineConfig({
  title: 'PythonBoot Starter',
  description: 'PythonBoot starter modules and integrations',
  locales: {
    root: { label: '简体中文', lang: 'zh-CN', link: '/zh/index.html' },
    en: { label: 'English', lang: 'en-US', link: '/en/index.html' },
  },
  themeConfig: {
    nav: [
      { text: '中文', link: '/zh/index.html' },
      { text: 'English', link: '/en/index.html' },
    ],
    sidebar: { '/zh/': zhSidebar, '/en/': enSidebar },
    socialLinks: [],
    search: { provider: 'local' },
  },
})
