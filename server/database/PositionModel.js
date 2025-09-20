class PositionModel {
  constructor(database) {
    this.db = database;
  }

  async getPosition(symbol) {
    const sql = 'SELECT * FROM positions WHERE symbol = ?';
    return await this.db.get(sql, [symbol]);
  }

  async getAllPositions() {
    const sql = 'SELECT * FROM positions ORDER BY symbol';
    return await this.db.all(sql);
  }

  async updatePosition(symbol, quantity, price, isClosing = false) {
    const currentPosition = await this.getPosition(symbol);
    
    if (!currentPosition) {
      // Create new position
      const sql = `
        INSERT INTO positions (symbol, quantity, avg_price, total_value, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
      `;
      const totalValue = quantity * price;
      return await this.db.run(sql, [symbol, quantity, price, totalValue]);
    } else {
      // Update existing position
      let newQuantity, newAvgPrice, newTotalValue;
      
      if (isClosing) {
        newQuantity = currentPosition.quantity - Math.abs(quantity);
        newAvgPrice = newQuantity === 0 ? 0 : currentPosition.avg_price;
        newTotalValue = newQuantity * newAvgPrice;
      } else {
        // Adding to position
        const oldValue = currentPosition.quantity * currentPosition.avg_price;
        const newValue = quantity * price;
        newTotalValue = oldValue + newValue;
        newQuantity = currentPosition.quantity + quantity;
        newAvgPrice = newQuantity !== 0 ? newTotalValue / newQuantity : 0;
      }
      
      const sql = `
        UPDATE positions 
        SET quantity = ?, avg_price = ?, total_value = ?, updated_at = CURRENT_TIMESTAMP
        WHERE symbol = ?
      `;
      return await this.db.run(sql, [newQuantity, newAvgPrice, newTotalValue, symbol]);
    }
  }

  async calculatePnL(symbol, currentPrice) {
    const position = await this.getPosition(symbol);
    if (!position || position.quantity === 0) {
      return 0;
    }
    
    const unrealizedPnL = (currentPrice - position.avg_price) * position.quantity;
    
    // Update the position with current PnL
    const sql = 'UPDATE positions SET pnl = ? WHERE symbol = ?';
    await this.db.run(sql, [unrealizedPnL, symbol]);
    
    return unrealizedPnL;
  }

  async closePosition(symbol) {
    const sql = 'DELETE FROM positions WHERE symbol = ?';
    return await this.db.run(sql, [symbol]);
  }
}

module.exports = PositionModel;