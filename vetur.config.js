/** @type {import('vls').VeturConfig} */
module.exports = {
  // Set project root for Vetur
  projects: [
    {
      // Path to frontend directory
      root: './cadaid_api/frontend',
      // Configure Vetur for Vue 3
      package: './package.json',
      jsconfig: './jsconfig.json',
      // Enable template interpolation service
      globalComponents: [
        './src/components/**/*.vue'
      ]
    }
  ]
} 