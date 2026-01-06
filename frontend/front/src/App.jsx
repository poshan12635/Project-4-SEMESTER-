import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import Navbar from './Navbar'
import {BrowserRouter,Routes,Route} from 'react-router-dom'
import Ai from "./Ai"
import Homepage from './Homepage'
import Backtest from './Backtest'

function App() {
  const [count, setCount] = useState(0)

  return (
    
    <>
    <Navbar/>
  
    <Routes>
      <Route path='/' element={<Homepage/>}/>
      <Route path="/Ai" element={<Ai/>}/>
      <Route path="/Backtest" element={<Backtest/>}/>
    </Routes>

    
  
      
    </>
  )
}

export default App
