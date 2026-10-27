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
          { text: 'Freestyle Moves', link: '/freestyle-moves' },
          { text: 'Edges & Crossovers', link: '/edges-crossovers' },
          { text: 'Turns & Footwork', link: '/turns-footwork' },
          {
            text: 'Spins',
            items: [
              { text: 'Spinning Fundamentals', link: '/spins/spins' },
              { text: 'Upright Spins', link: '/spins/upright-spins' },
              { text: 'Sit Spins', link: '/spins/sit-spins' },
              { text: 'Camel Spins', link: '/spins/camel-spins' },
              { text: 'Layback Spins', link: '/spins/layback-spins' },
              { text: 'Flying Spins', link: '/spins/flying-spins' },
              { text: 'Illusion, Star & Butterfly', link: '/spins/illusion-star-butterfly' },
              { text: 'Combination Spins', link: '/spins/combination-spins' }
            ]
          },
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
