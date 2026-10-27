export default {
  title: 'Figure Skating Guide',
  description: 'Quick-reference pages from The Complete Book of Figure Skating by Carole Shulman',
  lang: 'en-CA',
  cleanUrls: false,
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
          {
  text: 'Jumps',
  items: [
    { text: 'Fundamentals', link: '/jumps/jumps-fundamentals' },
    { text: 'Preparatory Jumps', link: '/jumps/jumps-preparatory' },
    { text: 'Edge Jumps', link: '/jumps/jumps-edge' },
    { text: 'Toe Jumps', link: '/jumps/jumps-toe' },
    { text: 'Combination Jumps', link: '/jumps/jumps-combinations' },
    { text: 'Multi-Rotational Jumps', link: '/jumps/jumps-multi-rotational' }
  ]
}
        ]
      }
    ],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/dodaydream/figure-skating-guide' }
    ]
  }
}
