import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'LectureMind Wiki',
  tagline: 'AI-Powered Lecture Video Analysis Platform',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://xuranus.github.io',
  baseUrl: '/LectureMind/',

  organizationName: 'XUranus',
  projectName: 'LectureMind',

  onBrokenLinks: 'warn',

  markdown: {
    format: 'detect',
  },

  i18n: {
    defaultLocale: 'zh-Hans',
    locales: ['zh-Hans'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/social-card.png',
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'LectureMind',
      logo: {
        alt: 'LectureMind Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: '文档',
        },
        {
          href: 'https://github.com/XUranus/LectureMind',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: '文档',
          items: [
            { label: '快速开始', to: '/getting-started' },
            { label: '架构概览', to: '/architecture' },
          ],
        },
        {
          title: '社区',
          items: [
            { label: 'GitHub', href: 'https://github.com/XUranus/LectureMind' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} LectureMind. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'typescript', 'bash', 'json', 'yaml'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
