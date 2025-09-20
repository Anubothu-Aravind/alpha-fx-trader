class TradeModel {
  constructor(database) {
    this.db = database;
  }

  async createTrade(trade) {
    const sql = `
      INSERT INTO trades (symbol, side, quantity, price, value, algorithm, status, pnl)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `;
    const params = [
      trade.symbol,
      trade.side,
      trade.quantity,
      trade.price,
      trade.value,
      trade.algorithm || null,
      trade.status || 'executed',
      trade.pnl || 0
    ];
    
    const result = await this.db.run(sql, params);
    return { id: result.id, ...trade };
  }

  async getTrades(symbol = null, limit = 100, offset = 0) {
    let sql = 'SELECT * FROM trades';
    let params = [];
    
    if (symbol) {
      sql += ' WHERE symbol = ?';
      params.push(symbol);
    }
    
    sql += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?';
    params.push(limit, offset);
    
    return await this.db.all(sql, params);
  }

  async getTradeById(id) {
    const sql = 'SELECT * FROM trades WHERE id = ?';
    return await this.db.get(sql, [id]);
  }

  async updateTrade(id, updates) {
    const fields = Object.keys(updates).map(key => `${key} = ?`).join(', ');
    const values = Object.values(updates);
    values.push(id);
    
    const sql = `UPDATE trades SET ${fields} WHERE id = ?`;
    return await this.db.run(sql, values);
  }

  async getTradingStats(date = null) {
    let sql = 'SELECT * FROM trading_stats';
    let params = [];
    
    if (date) {
      sql += ' WHERE date = ?';
      params.push(date);
    } else {
      sql += ' ORDER BY date DESC LIMIT 1';
    }
    
    return await this.db.get(sql, params);
  }

  async updateTradingStats(stats) {
    const sql = `
      INSERT OR REPLACE INTO trading_stats 
      (date, total_volume, total_trades, total_pnl, active_positions, updated_at)
      VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    `;
    const params = [
      stats.date || new Date().toISOString().split('T')[0],
      stats.total_volume || 0,
      stats.total_trades || 0,
      stats.total_pnl || 0,
      stats.active_positions || 0
    ];
    
    return await this.db.run(sql, params);
  }

  async getTotalVolume(date = null) {
    let sql = 'SELECT SUM(value) as total_volume FROM trades';
    let params = [];
    
    if (date) {
      sql += ' WHERE DATE(timestamp) = ?';
      params.push(date);
    }
    
    const result = await this.db.get(sql, params);
    return result ? result.total_volume || 0 : 0;
  }
}

module.exports = TradeModel;