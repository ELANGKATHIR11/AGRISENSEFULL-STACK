import React from 'react';
import TankStatus from './components/TankStatus';

function App() {
  return (
    <div className='p-6 bg-green-100 min-h-screen'>
      <h1 className='text-3xl font-bold text-green-800 mb-6'>
        🌾 AGRISENSE – Smart Agriculture Dashboard
      </h1>
      <TankStatus />
    </div>
  );
}

export default App;
