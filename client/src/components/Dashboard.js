import React from 'react';
import TradingControls from './TradingControls';
import PriceGrid from './PriceGrid';
import Blotter from './Blotter';
import Positions from './Positions';

const Dashboard = ({
  prices,
  trades,
  positions,
  tradingStatus,
  onStartTrading,
  onStopTrading
}) => {
  return (
    <div className="dashboard">
      <TradingControls
        tradingStatus={tradingStatus}
        onStart={onStartTrading}
        onStop={onStopTrading}
      />
      
      <PriceGrid prices={prices} />
      
      <Blotter trades={trades} />
      
      <Positions positions={positions} />
    </div>
  );
};

export default Dashboard;