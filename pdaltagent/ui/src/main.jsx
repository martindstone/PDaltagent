import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

import theme from './theme'

import {
  ColorModeScript,
  ChakraProvider,
} from '@chakra-ui/react'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ColorModeScript initialColorMode={theme.config.initialColorMode} useSystemColorMode={theme.config.useSystemColorMode} />
    <ChakraProvider>
      <App />
    </ChakraProvider>
  </React.StrictMode>,
)
