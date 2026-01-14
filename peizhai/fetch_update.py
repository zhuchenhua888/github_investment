import os
import re
import json
import sqlite3
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import argparse
import threading
import time

API_URL = 'https://www.jisilu.cn/data/cbnew/pre_list/'
DB_FILE = 'cb_data.db'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.jisilu.cn/',
}


def today_str():
    """YYYY-MM-DD（用于判断当天是否已更新）"""
    return datetime.now().strftime('%Y-%m-%d')


def now_str():
    """YYYY-MM-DD HH:MM:SS（用于日志与 last_update）"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def parse_progress_full(pf: str):
    """解析 progress_full 提取各阶段日期"""
    board_dt = shareholder_dt = accept_dt = committee_dt = register_dt = None
    if not pf:
        return board_dt, shareholder_dt, accept_dt, committee_dt, register_dt
    for line in pf.split('\n'):
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^(\d{4}-\d{2}-\d{2})\s+(.*)$', line)
        if not m:
            continue
        dt, step = m.group(1), m.group(2)
        if '董事会预案' in step:
            board_dt = dt
        elif '股东大会通过' in step:
            shareholder_dt = dt
        elif '交易所受理' in step:
            accept_dt = dt
        elif '上市委通过' in step:
            committee_dt = dt
        elif '同意注册' in step:
            register_dt = dt
    return board_dt, shareholder_dt, accept_dt, committee_dt, register_dt


def sanitize_progress_nm(s: str):
    """清理 progress_nm 的 HTML 标记"""
    if not s:
        return ''
    s = re.sub(r'<br\s*/?>', ' ', s, flags=re.I)
    s = re.sub(r'<[^>]+>', '', s)
    return s.strip()


def http_json(url: str, method: str = 'GET'):
    """HTTP 请求并返回 JSON"""
    req = Request(url, headers=HEADERS, method=method)
    try:
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
            return json.loads(data.decode('utf-8', errors='ignore'))
    except (URLError, HTTPError) as e:
        raise RuntimeError(f'网络错误: {e}')


def fetch_json():
    return http_json(API_URL, 'GET')


def ensure_schema(conn: sqlite3.Connection):
    """确保表结构与复合主键，必要时重建并迁移数据"""
    conn.execute(
        '''CREATE TABLE IF NOT EXISTS cb (
            bond_id TEXT NOT NULL DEFAULT '',
            bond_nm TEXT,
            stock_id TEXT NOT NULL,
            stock_nm TEXT,
            amount TEXT,
            rating_cd TEXT,
            progress_dt TEXT,
            progress_nm TEXT,
            board_dt TEXT,
            shareholder_dt TEXT,
            accept_dt TEXT,
            committee_dt TEXT,
            register_dt TEXT,
            apply_date TEXT,
            apply_cd TEXT,
            list_date TEXT,
            maturity_dt TEXT,
            delist_dt TEXT,
            delist_notes TEXT,
            PRIMARY KEY(stock_id, bond_id)
        );'''
    )
    conn.execute(
        '''CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );'''
    )
    # 迁移旧表结构：补充缺失列并重建为复合主键
    info = list(conn.execute("PRAGMA table_info('cb')"))
    cols = {row[1] for row in info}
    for col in [
        'bond_id','bond_nm','progress_dt','progress_nm','board_dt','shareholder_dt','accept_dt','committee_dt','register_dt',
        'apply_date','amount','rating_cd','apply_cd','list_date','maturity_dt','delist_dt','delist_notes'
    ]:
        if col not in cols:
            conn.execute(f"ALTER TABLE cb ADD COLUMN {col} TEXT")
    pk_cols = {row[1] for row in info if row[5]}
    need_rebuild = pk_cols != {'stock_id', 'bond_id'}
    if need_rebuild:
        conn.execute('PRAGMA foreign_keys=off')
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS cb_new (
                bond_id TEXT NOT NULL DEFAULT '',
                bond_nm TEXT,
                stock_id TEXT NOT NULL,
                stock_nm TEXT,
                amount TEXT,
                rating_cd TEXT,
                progress_dt TEXT,
                progress_nm TEXT,
                board_dt TEXT,
                shareholder_dt TEXT,
                accept_dt TEXT,
                committee_dt TEXT,
                register_dt TEXT,
                apply_date TEXT,
                apply_cd TEXT,
                list_date TEXT,
                maturity_dt TEXT,
                delist_dt TEXT,
                delist_notes TEXT,
                PRIMARY KEY(stock_id, bond_id)
            );'''
        )
        apply_col = 'apply_date' if 'apply_date' in cols else ('apply_dt' if 'apply_dt' in cols else None)
        sel_apply = apply_col if apply_col else 'NULL'
        conn.execute(
            f'''INSERT INTO cb_new(bond_id,bond_nm,stock_id,stock_nm,amount,rating_cd,progress_dt,progress_nm,board_dt,shareholder_dt,accept_dt,committee_dt,register_dt,apply_date,apply_cd,list_date,maturity_dt,delist_dt,delist_notes)
                SELECT COALESCE(bond_id,''), bond_nm, stock_id, stock_nm, amount, rating_cd, progress_dt, progress_nm, board_dt, shareholder_dt, accept_dt, committee_dt, register_dt, {sel_apply}, apply_cd, list_date, maturity_dt, delist_dt, delist_notes FROM cb'''
        )
        conn.execute('DROP TABLE cb')
        conn.execute('ALTER TABLE cb_new RENAME TO cb')
        conn.execute('PRAGMA foreign_keys=on')
    conn.commit()


def has_updated_today(db_path: str) -> bool:
    """根据 meta.last_update 的日期部分判断是否已更新当天"""
    try:
        conn = sqlite3.connect(db_path)
        try:
            ensure_schema(conn)
            cur = conn.execute("SELECT value FROM meta WHERE key='last_update'")
            row = cur.fetchone()
            return bool(row and str(row[0])[:10] == today_str())
        finally:
            conn.close()
    except Exception:
        return False


def fetch_and_update(db_path: str):
    """融合各接口数据并写入数据库与 last_update"""
    t0 = time.time()
    print(f'[{now_str()}] 开始更新流程...')

    t1 = time.time()
    js = fetch_json()
    print(f'[{now_str()}] 获取待发转债数据耗时: {time.time() - t1:.2f}s')

    rows = js.get('rows', [])
    conn = sqlite3.connect(db_path)
    try:
        ensure_schema(conn)
        sql = (
            'INSERT INTO cb(bond_id,bond_nm,stock_id,stock_nm,amount,rating_cd,progress_dt,progress_nm,board_dt,shareholder_dt,accept_dt,committee_dt,register_dt,apply_date,apply_cd,list_date,maturity_dt,delist_dt,delist_notes) '
            'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '
            'ON CONFLICT(stock_id,bond_id) DO UPDATE SET '
            'bond_id=excluded.bond_id, bond_nm=excluded.bond_nm, stock_nm=excluded.stock_nm, amount=excluded.amount, rating_cd=COALESCE(excluded.rating_cd, rating_cd), progress_dt=excluded.progress_dt, progress_nm=excluded.progress_nm, '
            'board_dt=COALESCE(excluded.board_dt, board_dt), shareholder_dt=COALESCE(excluded.shareholder_dt, shareholder_dt), accept_dt=COALESCE(excluded.accept_dt, accept_dt), committee_dt=COALESCE(excluded.committee_dt, committee_dt), register_dt=COALESCE(excluded.register_dt, register_dt), '
            'apply_date=COALESCE(excluded.apply_date, apply_date), apply_cd=COALESCE(excluded.apply_cd, apply_cd), '
            'list_date=COALESCE(list_date, excluded.list_date), maturity_dt=COALESCE(maturity_dt, excluded.maturity_dt), delist_dt=COALESCE(excluded.delist_dt, delist_dt), delist_notes=COALESCE(excluded.delist_notes, delist_notes)'
        )
        print(f'待发转债：{len(rows)} rows to update')
        for item in rows:
            cell = item.get('cell', {})
            pf = cell.get('progress_full') or ''
            board_dt, shareholder_dt, accept_dt, committee_dt, register_dt = parse_progress_full(pf)
            apply_date = cell.get('apply_date') or None
            bond_id_val = (cell.get('bond_id') or '')
            bond_nm_val = cell.get('bond_nm') or None
            stock_id_val = str(cell.get('stock_id') or item.get('id') or '')
            stock_nm_val = cell.get('stock_nm') or ''
            amount_val = cell.get('amount') or None
            rating_cd_val = cell.get('rating_cd') or None
            progress_dt_val = cell.get('progress_dt') or None
            progress_nm_val = sanitize_progress_nm(cell.get('progress_nm') or '')
            apply_cd_val = cell.get('apply_cd') or None
            list_date_val = cell.get('list_date') or None

            # 将仅有 stock_id 的老记录“升级”为包含 bond_id 的记录，避免重复两条
            if bond_id_val:
                # 若同键已存在则不做升级，后续 UPSERT 会合并；并删除空 bond_id 的旧行
                conn.execute(
                    'UPDATE cb SET bond_id=?, bond_nm=?, stock_nm=?, amount=?, rating_cd=?, progress_dt=?, progress_nm=?, board_dt=?, shareholder_dt=?, accept_dt=?, committee_dt=?, register_dt=?, apply_date=?, apply_cd=?, list_date=? '
                    'WHERE stock_id=? AND bond_id=? AND NOT EXISTS (SELECT 1 FROM cb WHERE stock_id=? AND bond_id=?)',
                    (
                        bond_id_val, bond_nm_val, stock_nm_val, amount_val, rating_cd_val,
                        progress_dt_val, progress_nm_val, board_dt, shareholder_dt, accept_dt, committee_dt, register_dt,
                        apply_date, apply_cd_val, list_date_val, stock_id_val, '', stock_id_val, bond_id_val
                    )
                )
                cur_old = conn.execute(
                    'SELECT board_dt,shareholder_dt,accept_dt,committee_dt,register_dt, stock_nm,amount,rating_cd,progress_dt,progress_nm,apply_date,apply_cd,list_date FROM cb WHERE stock_id=? AND bond_id=?',
                    (stock_id_val, '')
                )
                old_row = cur_old.fetchone()
                cur_new = conn.execute(
                    'SELECT board_dt,shareholder_dt,accept_dt,committee_dt,register_dt FROM cb WHERE stock_id=? AND bond_id=?',
                    (stock_id_val, bond_id_val)
                )
                new_row = cur_new.fetchone()
                if old_row and new_row and (
                    (old_row[0] or '') == (new_row[0] or '') and
                    (old_row[1] or '') == (new_row[1] or '') and
                    (old_row[2] or '') == (new_row[2] or '') and
                    (old_row[3] or '') == (new_row[3] or '') and
                    (old_row[4] or '') == (new_row[4] or '')
                ):
                    conn.execute(
                        'UPDATE cb SET stock_nm=COALESCE(stock_nm, ?), amount=COALESCE(amount, ?), rating_cd=COALESCE(rating_cd, ?), progress_dt=COALESCE(progress_dt, ?), progress_nm=COALESCE(progress_nm, ?), '
                        'board_dt=COALESCE(board_dt, ?), shareholder_dt=COALESCE(shareholder_dt, ?), accept_dt=COALESCE(accept_dt, ?), committee_dt=COALESCE(committee_dt, ?), register_dt=COALESCE(register_dt, ?), '
                        'apply_date=COALESCE(apply_date, ?), apply_cd=COALESCE(apply_cd, ?), list_date=COALESCE(list_date, ?) WHERE stock_id=? AND bond_id=?',
                        (
                            old_row[5], old_row[6], old_row[7], old_row[8], old_row[9],
                            old_row[0], old_row[1], old_row[2], old_row[3], old_row[4],
                            old_row[10], old_row[11], old_row[12], stock_id_val, bond_id_val
                        )
                    )
                    conn.execute('DELETE FROM cb WHERE stock_id=? AND bond_id=?', (stock_id_val, ''))

            rec = (
                bond_id_val,
                bond_nm_val,
                stock_id_val,
                stock_nm_val,
                amount_val,
                rating_cd_val,
                progress_dt_val,
                progress_nm_val,
                board_dt,
                shareholder_dt,
                accept_dt,
                committee_dt,
                register_dt,
                apply_date,
                apply_cd_val,
                list_date_val,
                None,
                None,
                None,
            )
            conn.execute(sql, rec)
        print(f'[{now_str()}] 处理待发转债({len(rows)}条)耗时: {time.time() - t1:.2f}s (含获取)')

        # 合并上市后信息（list_dt/maturity_dt），仅在本表缺少上市日期时写入list_date
        t3 = time.time()
        try:
            js_listed = fetch_listed()
            print(f'[{now_str()}] 获取上市转债数据耗时: {time.time() - t3:.2f}s')

            rows_listed = js_listed.get('rows', [])
            sql_listed = (
                'INSERT INTO cb(bond_id,stock_id,bond_nm,stock_nm,rating_cd,list_date,maturity_dt) '
                'VALUES(?,?,?,?,?,?,?) '
                'ON CONFLICT(stock_id,bond_id) DO UPDATE SET '
                'rating_cd=COALESCE(excluded.rating_cd, rating_cd), maturity_dt=COALESCE(excluded.maturity_dt, maturity_dt), '
                'list_date=COALESCE(list_date, excluded.list_date)'
            )
            print(f'上市转债：rows_listed: {len(rows_listed)}')
            for it in rows_listed:
                c2 = it.get('cell', {})
                bid = (c2.get('bond_id') or '')
                sid = str(c2.get('stock_id') or it.get('id') or '')
                rec2 = (
                    bid,
                    sid,
                    c2.get('bond_nm') or None,
                    c2.get('stock_nm') or None,
                    c2.get('rating_cd') or None,
                    c2.get('list_dt') or None,
                    c2.get('maturity_dt') or None,
                )
                conn.execute(sql_listed, rec2)
            print(f'[{now_str()}] 处理上市转债({len(rows_listed)}条)耗时: {time.time() - t3:.2f}s (含获取)')
        except Exception as e:
            print(f'[{now_str()}] 获取/处理上市转债失败: {e}')
            pass

        # 合并退市与到期信息
        t5 = time.time()
        try:
            js2 = fetch_delisted()
            print(f'[{now_str()}] 获取退市转债数据耗时: {time.time() - t5:.2f}s')
            rows2 = js2.get('rows', [])
            print(f'退市转债：rows2: {len(rows2)}')
            for it in rows2:
                cell2 = it.get('cell', {})
                bid = cell2.get('bond_id') or None
                if not bid:
                    continue
                maturity_dt = cell2.get('maturity_dt') or None
                delist_dt = cell2.get('delist_dt') or None
                delist_notes = cell2.get('delist_notes') or None
                issue_dt = cell2.get('issue_dt') or None
                first_dt = cell2.get('first_dt') or None
                conn.execute(
                    'UPDATE cb SET apply_date=COALESCE(apply_date, ?), list_date=COALESCE(list_date, ?), maturity_dt=COALESCE(maturity_dt, ?), delist_dt=COALESCE(delist_dt, ?), delist_notes=COALESCE(delist_notes, ?) WHERE bond_id=?',
                    (issue_dt, first_dt, maturity_dt, delist_dt, delist_notes, bid)
                )
            print(f'[{now_str()}] 处理退市转债({len(rows2)}条)耗时: {time.time() - t5:.2f}s (含获取)')
        except Exception as e:
            print(f'[{now_str()}] 获取/处理退市转债失败: {e}')
            pass
        
        t7 = time.time()
        ts = now_str()
        conn.execute('INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=?', ('last_update', ts, ts))
        conn.commit()
        print(f'[{now_str()}] 数据库提交耗时: {time.time() - t7:.2f}s')
    finally:
        conn.close()
    print(f'[{now_str()}] 总更新耗时: {time.time() - t0:.2f}s')


def fetch_delisted():
    """退市信息接口（POST）"""
    url = 'https://www.jisilu.cn/data/cbnew/delisted/?___jsl=LST___t=' + str(int(time.time()*1000))
    return http_json(url, 'POST')


def fetch_listed():
    """上市后信息接口（POST）"""
    url = 'https://www.jisilu.cn/data/cbnew/cb_list_new/?___jsl=LST___t=' + str(int(time.time()*1000))
    headers = dict(HEADERS)
    cookie = os.environ.get('JISILU_COOKIE') or None
    if not cookie:
        try:
            cookie_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookie.txt')
            if os.path.exists(cookie_path):
                with open(cookie_path, 'r', encoding='utf-8') as f:
                    txt = f.read().strip()
                    if txt:
                        cookie = txt
        except Exception:
            cookie = cookie
    if cookie:
        headers['Cookie'] = cookie
    print(f'[{now_str()}] fetch_listed: 准备请求 URL: {url}')
    req = Request(url, headers=headers, method='POST')
    try:
        t_req = time.time()
        with urlopen(req, timeout=30) as resp:
            print(f'[{now_str()}] fetch_listed: 连接建立耗时: {time.time() - t_req:.2f}s')
            t_read = time.time()
            data = resp.read()
            print(f'[{now_str()}] fetch_listed: 数据读取耗时: {time.time() - t_read:.2f}s, 大小: {len(data)} bytes')
            return json.loads(data.decode('utf-8', errors='ignore'))
    except (URLError, HTTPError) as e:
        raise RuntimeError(f'网络错误: {e}')


class Handler(SimpleHTTPRequestHandler):
    """本地服务：提供静态资源与 /update 更新接口"""
    def __init__(self, *args, **kwargs):
        directory = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        if self.path.startswith('/update'):
            try:
                fetch_and_update(os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILE))
                body = json.dumps({'ok': True, 'updated': now_str()}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                body = json.dumps({'ok': False, 'error': str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/edit_row':
            try:
                length = int(self.headers.get('content-length', 0))
                data = json.loads(self.rfile.read(length))
                
                old_stock_id = data.get('old_stock_id')
                old_bond_id = data.get('old_bond_id')
                new_data = data.get('new_data', {})
                
                if old_stock_id is None: # bond_id can be empty string
                    raise ValueError("Missing old_stock_id")

                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILE)
                conn = sqlite3.connect(db_path)
                try:
                    set_parts = []
                    params = []
                    for k, v in new_data.items():
                        set_parts.append(f"{k}=?")
                        params.append(v)
                    
                    if not set_parts:
                        raise ValueError("No data to update")

                    params.append(old_stock_id)
                    params.append(old_bond_id if old_bond_id is not None else '')
                    
                    sql = f"UPDATE cb SET {', '.join(set_parts)} WHERE stock_id=? AND bond_id=?"
                    conn.execute(sql, params)
                    conn.commit()
                finally:
                    conn.close()

                body = json.dumps({'ok': True}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                body = json.dumps({'ok': False, 'error': str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(body)
        else:
            self.send_error(404)


def main():
    """命令行入口：一次更新、HTTP 服务、定时更新（整点或指定）"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve', action='store_true', help='启动本地服务器并提供 /update 接口')
    parser.add_argument('--port', type=int, default=8000, help='本地服务器端口')
    parser.add_argument('--once', action='store_true', help='仅抓取一次并退出')
    parser.add_argument('--schedule', type=str, help='每天固定时间执行更新，格式HH:MM')
    args = parser.parse_args()

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILE)
    if args.once:
        fetch_and_update(db_path)
        print(f'更新完成: {db_path}')
        return
    sched_thread = None
    sched_time = args.schedule
    if args.serve and not sched_time:
        def worker():
            while True:
                now = datetime.now()
                next_run = now.replace(minute=0, second=0, microsecond=0)
                if next_run <= now:
                    next_run = next_run + timedelta(hours=1)
                wait = (next_run - now).total_seconds()
                time.sleep(max(1, int(wait)))
                try:
                    if 8 <= next_run.hour <= 18:
                        fetch_and_update(db_path)
                        print(f'整点更新完成: {db_path} at {now_str()}')
                    else:
                        print(f'非时段跳过: {now_str()}')
                except Exception as e:
                    print(f'整点更新失败: {e}')
        sched_thread = threading.Thread(target=worker, daemon=True)
        sched_thread.start()
    elif sched_time:
        hh, mm = sched_time.split(':')
        run_hour = int(hh)
        run_min = int(mm)
        def worker():
            while True:
                now = datetime.now()
                next_run = now.replace(hour=run_hour, minute=run_min, second=0, microsecond=0)
                if next_run <= now:
                    next_run = next_run + timedelta(days=1)
                wait = (next_run - now).total_seconds()
                time.sleep(max(1, int(wait)))
                try:
                    fetch_and_update(db_path)
                    print(f'定时更新完成: {db_path} at {now_str()}')
                except Exception as e:
                    print(f'定时更新失败: {e}')
        sched_thread = threading.Thread(target=worker, daemon=True)
        sched_thread.start()
    if args.serve:
        httpd = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
        print(f'服务已启动: http://127.0.0.1:{args.port}/  (数据库: {db_path})')
        try:
            fetch_and_update(db_path)
            print(f'服务启动时已自动更新: {now_str()}')
        except Exception as e:
            print(f'服务启动自动更新失败: {e}')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
    else:
        if sched_time:
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
        else:
            fetch_and_update(db_path)
            print(f'更新完成: {db_path}')


if __name__ == '__main__':
    main()
