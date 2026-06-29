from __future__ import annotations

from ..chain.blockchain import Blockchain


class ExplorerRenderer:

    def render_index(self, blockchain: Blockchain) -> str:
        blocks_html = ""
        for block in reversed(blockchain._chain[-10:]):
            tx_count = len(block.transactions)
            reward = sum(
                o.amount
                for tx in block.transactions
                for o in tx.outputs
                if tx.memo == "coinbase" or
                tx.inputs[0].tx_id == "0" * 64
            )
            blocks_html += f"""
<tr onclick="window.location='/block/{block.header.height}'"
    style="cursor:pointer">
  <td>{block.header.height}</td>
  <td class="hash">{block.hash[:24]}...</td>
  <td>{tx_count}</td>
  <td>{block.header.difficulty}</td>
  <td>{block.header.nonce:,}</td>
  <td class="green">{reward:.1f} NLC</td>
</tr>"""

        last_hash = blockchain.last_block.hash if blockchain.last_block else "—"
        pct = (blockchain.total_minted / 18_000_000) * 100

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NullCoin Explorer</title>
{self._style()}
</head>
<body>
{self._nav()}
<div class="container">
  <div class="hero">
    <h2>NullCoin Block Explorer</h2>
    <p class="subtitle">Privacy-first blockchain — every transaction private by default</p>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Chain Height</div>
      <div class="stat-value">{blockchain.height:,}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Total Minted</div>
      <div class="stat-value">{blockchain.total_minted:,.1f} NLC</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Max Supply</div>
      <div class="stat-value">18,000,000 NLC</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Supply Minted</div>
      <div class="stat-value">{pct:.4f}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Difficulty</div>
      <div class="stat-value">{blockchain._difficulty}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Pending Txs</div>
      <div class="stat-value">{blockchain.pending_count}</div>
    </div>
  </div>

  <div class="card">
    <h3>Latest Blocks</h3>
    <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Height</th>
          <th>Hash</th>
          <th>Txs</th>
          <th>Difficulty</th>
          <th>Nonce</th>
          <th>Reward</th>
        </tr>
      </thead>
      <tbody>
        {blocks_html}
      </tbody>
    </table>
    </div>
  </div>

  <div class="card">
    <h3>Search</h3>
    <div class="search-row">
      <input type="text" id="search"
             placeholder="Block height or address..."
             class="search-input">
      <button onclick="doSearch()" class="btn">Search</button>
    </div>
  </div>

</div>
{self._footer()}
<script>
function doSearch() {{
  const q = document.getElementById('search').value.trim();
  if (!q) return;
  if (!isNaN(q)) {{
    window.location = '/block/' + q;
  }} else {{
    window.location = '/address/' + q;
  }}
}}
document.getElementById('search').addEventListener('keypress', function(e) {{
  if (e.key === 'Enter') doSearch();
}});
</script>
</body>
</html>"""

    def render_block(self, blockchain: Blockchain, height: int) -> str:
        if height >= len(blockchain._chain):
            return self._error("Block not found")

        block = blockchain._chain[height]
        txs_html = ""
        for tx in block.transactions:
            is_coinbase = tx.inputs[0].tx_id == "0" * 64
            label = "COINBASE" if is_coinbase else "TX"
            color = "green" if is_coinbase else "blue"
            outputs_html = "".join([
                f'<div class="output">'
                f'<span class="addr">{o.address[:20]}...</span>'
                f'<span class="{color}">{o.amount:.4f} NLC</span>'
                f'</div>'
                for o in tx.outputs
            ])
            txs_html += f"""
<div class="tx-card">
  <div class="tx-header">
    <span class="badge {color}">{label}</span>
    <span class="hash">{tx.tx_id[:32]}...</span>
  </div>
  <div class="tx-outputs">{outputs_html}</div>
</div>"""

        prev_link = (
            f'<a href="/block/{height-1}" class="btn-sm">← Prev</a>'
            if height > 0 else ""
        )
        next_link = (
            f'<a href="/block/{height+1}" class="btn-sm">Next →</a>'
            if height < blockchain.height - 1 else ""
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Block #{height} — NullCoin Explorer</title>
{self._style()}
</head>
<body>
{self._nav()}
<div class="container">
  <div class="page-header">
    <h2>Block #{height}</h2>
    <div class="nav-buttons">{prev_link} {next_link}</div>
  </div>

  <div class="card">
    <h3>Block Details</h3>
    <table class="detail-table">
      <tr><td>Height</td><td>{block.header.height}</td></tr>
      <tr><td>Hash</td><td class="hash mono">{block.hash}</td></tr>
      <tr><td>Previous</td>
          <td class="hash mono">{block.header.previous_hash}</td></tr>
      <tr><td>Merkle Root</td>
          <td class="hash mono">{block.header.merkle_root}</td></tr>
      <tr><td>Difficulty</td><td>{block.header.difficulty}</td></tr>
      <tr><td>Nonce</td><td>{block.header.nonce:,}</td></tr>
      <tr><td>Transactions</td><td>{len(block.transactions)}</td></tr>
    </table>
  </div>

  <div class="card">
    <h3>Transactions ({len(block.transactions)})</h3>
    {txs_html}
  </div>
</div>
{self._footer()}
</body>
</html>"""

    def render_address(self, blockchain: Blockchain, address: str) -> str:
        balance = blockchain.get_balance(address)
        txs_html = ""
        tx_count = 0

        for block in blockchain._chain:
            for tx in block.transactions:
                involved = any(
                    o.address == address for o in tx.outputs
                )
                if involved:
                    tx_count += 1
                    outputs_html = "".join([
                        f'<div class="output">'
                        f'<span class="addr">{o.address[:20]}...</span>'
                        f'<span class="green">{o.amount:.4f} NLC</span>'
                        f'</div>'
                        for o in tx.outputs if o.address == address
                    ])
                    txs_html += f"""
<div class="tx-card">
  <div class="tx-header">
    <span class="hash">Block #{block.header.height}</span>
    <span class="hash">{tx.tx_id[:24]}...</span>
  </div>
  <div class="tx-outputs">{outputs_html}</div>
</div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Address — NullCoin Explorer</title>
{self._style()}
</head>
<body>
{self._nav()}
<div class="container">
  <h2>Address</h2>

  <div class="card">
    <div class="addr-display mono">{address}</div>
    <div class="stats-grid" style="margin-top:16px">
      <div class="stat-card">
        <div class="stat-label">Balance</div>
        <div class="stat-value green">{balance:.4f} NLC</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Transactions</div>
        <div class="stat-value">{tx_count}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h3>Transaction History</h3>
    {txs_html if txs_html else '<p class="muted">No transactions found.</p>'}
  </div>
</div>
{self._footer()}
</body>
</html>"""

    def _error(self, msg: str) -> str:
        return f"""<!DOCTYPE html>
<html><head><title>Error</title>{self._style()}</head>
<body>{self._nav()}
<div class="container">
  <div class="card">
    <h2>404 — {msg}</h2>
    <a href="/" class="btn">Back to Explorer</a>
  </div>
</div>{self._footer()}</body></html>"""

    def _nav(self) -> str:
        return """
<nav>
  <div class="nav-inner">
    <a href="/" class="nav-brand">⚡ NullCoin Explorer</a>
    <div class="nav-links">
      <a href="/">Blocks</a>
      <a href="https://github.com/painhub-ui/nullcoin"
         target="_blank">GitHub</a>
    </div>
  </div>
</nav>"""

    def _footer(self) -> str:
        return """
<footer>
  <p>NullCoin (NLC) — Privacy is not a feature. It is the foundation.</p>
  <p><a href="https://github.com/painhub-ui/nullcoin">
    github.com/painhub-ui/nullcoin</a></p>
</footer>"""

    def _style(self) -> str:
        return """<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'JetBrains Mono',monospace;background:#0d1117;
     color:#c9d1d9;min-height:100vh}
nav{background:#161b22;border-bottom:1px solid #30363d;
    padding:12px 24px}
.nav-inner{display:flex;align-items:center;
           justify-content:space-between;max-width:1100px;margin:0 auto}
.nav-brand{color:#58a6ff;text-decoration:none;font-size:16px;
           font-weight:700}
.nav-links a{color:#8b949e;text-decoration:none;margin-left:20px;
             font-size:13px}
.nav-links a:hover{color:#c9d1d9}
.container{max-width:1100px;margin:0 auto;padding:24px 16px}
.hero{text-align:center;padding:32px 0 24px}
.hero h2{font-size:24px;color:#e6edf3;margin-bottom:8px}
.subtitle{color:#8b949e;font-size:13px}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
            gap:12px;margin-bottom:20px}
.stat-card{background:#161b22;border:1px solid #30363d;border-radius:8px;
           padding:16px;text-align:center}
.stat-label{font-size:11px;color:#8b949e;text-transform:uppercase;
            letter-spacing:.5px;margin-bottom:6px}
.stat-value{font-size:18px;font-weight:700;color:#e6edf3}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;
      padding:20px;margin-bottom:20px}
.card h3{font-size:14px;color:#8b949e;text-transform:uppercase;
         letter-spacing:.5px;margin-bottom:16px}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:8px 12px;color:#8b949e;font-size:11px;
   text-transform:uppercase;border-bottom:1px solid #30363d}
td{padding:10px 12px;border-bottom:1px solid #21262d;font-size:13px}
tr:hover td{background:#1c2128}
tr:last-child td{border-bottom:none}
.hash{font-family:monospace;color:#79c0ff;font-size:12px}
.green{color:#3fb950}
.blue{color:#58a6ff}
.muted{color:#8b949e;font-size:13px}
.mono{font-family:monospace;word-break:break-all;font-size:12px}
.search-row{display:flex;gap:8px}
.search-input{flex:1;background:#0d1117;border:1px solid #30363d;
              border-radius:6px;padding:10px 14px;color:#c9d1d9;
              font-size:14px;font-family:monospace}
.search-input:focus{outline:none;border-color:#58a6ff}
.btn{background:#1f6feb;color:#fff;border:none;padding:10px 20px;
     border-radius:6px;cursor:pointer;font-size:13px;text-decoration:none}
.btn:hover{background:#388bfd}
.btn-sm{background:#21262d;color:#c9d1d9;border:1px solid #30363d;
        padding:6px 12px;border-radius:6px;text-decoration:none;
        font-size:12px}
.btn-sm:hover{background:#30363d}
.page-header{display:flex;align-items:center;
             justify-content:space-between;margin-bottom:20px}
.page-header h2{font-size:20px;color:#e6edf3}
.nav-buttons{display:flex;gap:8px}
.detail-table{width:100%;font-size:13px}
.detail-table td:first-child{color:#8b949e;width:120px;
                              padding:8px 0;vertical-align:top}
.detail-table td:last-child{padding:8px 0}
.detail-table tr{border-bottom:1px solid #21262d}
.detail-table tr:last-child{border-bottom:none}
.tx-card{border:1px solid #30363d;border-radius:6px;
         padding:14px;margin-bottom:12px}
.tx-header{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.badge{font-size:10px;padding:2px 8px;border-radius:4px;font-weight:700}
.badge.green{background:#0d2d0d;color:#3fb950;border:1px solid #3fb950}
.badge.blue{background:#0d1d3d;color:#58a6ff;border:1px solid #58a6ff}
.output{display:flex;justify-content:space-between;padding:4px 0;
        font-size:12px;border-bottom:1px solid #21262d}
.output:last-child{border-bottom:none}
.addr{color:#8b949e;font-family:monospace}
.addr-display{background:#0d1117;border:1px solid #30363d;
              border-radius:6px;padding:12px;word-break:break-all;
              font-size:12px;color:#79c0ff}
footer{text-align:center;padding:32px 16px;font-size:12px;
       color:#8b949e;border-top:1px solid #21262d;margin-top:20px}
footer a{color:#58a6ff;text-decoration:none}
</style>"""
