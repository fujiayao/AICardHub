// Adapted from the official template; mobile design coordinates are 390px.
export default { plugins: { autoprefixer: {}, 'postcss-mobile-forever': {
  appSelector: '#app', viewportWidth: 390, maxDisplayWidth: 480, border: true,
  rootContainingBlockSelectorList: ['.van-tabbar', '.van-popup', '.van-popup--bottom', '.van-popup--top', '.bottom-bar', '.chat-composer'],
} } }
