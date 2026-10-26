import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Figure Skating Guide',
  description: 'Quick-reference pages from The Complete Book of Figure Skating by Carole Shulman',
  lang: 'en',
  base: "./",
  cleanUrls: false,
  srcDir: './docs',
  outDir: '../dist',
  srcExclude: ['**/index.html'],
  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
    ],
    sidebar: [
      {
        text: 'Guide',
        items: [
          { text: 'Home', link: '/' },
          { text: 'Stops', link: '/stops' },
          { text: 'Stroking', link: '/stroking' },
          { text: 'Edges & Crossovers', link: '/edges-crossovers' },
          { text: 'Turns & Footwork', link: '/turns-footwork' },
        ]
      }
    ],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/dodaydream/figure-skating-guide' }
    ]
  }
})
