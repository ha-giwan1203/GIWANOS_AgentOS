module.exports = {
  apps: [
    {
      name: 'velos_dashboard',
      script: 'streamlit',
      args: 'run scripts/velos_dashboard.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --server.runOnSave=false --logger.level=info',
      cwd: process.cwd(),
      env: {
        TZ: 'Asia/Seoul',
        LANG: 'ko_KR.UTF-8',
        LC_TIME: 'ko_KR.UTF-8',
        PYTHONPATH: process.cwd(),
        NODE_ENV: 'production'
      },
      error_file: './data/logs/dashboard-error.log',
      out_file: './data/logs/dashboard-out.log',
      log_file: './data/logs/dashboard-combined.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 1000
    },
    {
      name: 'velos-dashboard',
      script: 'streamlit',  
      args: 'run scripts/velos_dashboard.py --server.port=8502 --server.address=0.0.0.0 --server.headless=true --server.runOnSave=false --logger.level=info',
      cwd: process.cwd(),
      env: {
        TZ: 'Asia/Seoul',
        LANG: 'ko_KR.UTF-8', 
        LC_TIME: 'ko_KR.UTF-8',
        PYTHONPATH: process.cwd(),
        NODE_ENV: 'production'
      },
      error_file: './data/logs/dashboard2-error.log',
      out_file: './data/logs/dashboard2-out.log',
      log_file: './data/logs/dashboard2-combined.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s', 
      restart_delay: 1000
    },
    {
      name: 'autosave_runner',
      script: 'python3',
      args: 'scripts/autosave_runner.py',
      cwd: process.cwd(),
      env: {
        TZ: 'Asia/Seoul',
        LANG: 'ko_KR.UTF-8',
        LC_TIME: 'ko_KR.UTF-8', 
        PYTHONPATH: process.cwd(),
        NODE_ENV: 'production'
      },
      error_file: './data/logs/autosave-error.log',
      out_file: './data/logs/autosave-out.log',
      log_file: './data/logs/autosave-combined.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 1000
    }
  ]
};