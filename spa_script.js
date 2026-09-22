// --- VARIABLES ---
const appUrl = "<?= appUrl ?>";
const username = localStorage.getItem("kliqify_username") || "";
const isAdmin = <?= isAdmin ?>;
let currentPage = 'dashboard';
let historyLoaded = false;
let adminLoaded = false;

// --- PAGE TITLES CONFIG ---
const pageTitles = {
  dashboard: { heading: 'Dashboard Overview', subtitle: 'Welcome back, ' + username },
  wallet: { heading: 'Wallet', subtitle: 'Kelola saldo dan tarik dana Anda' },
  history: { heading: 'History', subtitle: 'Riwayat pendapatan dan penarikan' },
  settings: { heading: 'Settings', subtitle: 'Pengaturan akun Anda' },
  admin: { heading: 'Admin Panel', subtitle: 'Kelola Seluruh Pengguna & Penarikan' }
};

// --- SPA NAVIGATION ---
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  sidebar.classList.toggle('active');
  overlay.classList.toggle('show');
}

function navigateTo(page) {
  // Auto-close sidebar on mobile when navigating
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebar.classList.contains('active')) {
    sidebar.classList.remove('active');
    overlay.classList.remove('show');
  }

  // Hide all pages
  document.querySelectorAll('.page-section').forEach(el => el.classList.remove('active'));

  // Remove active from all nav items
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

  // Show target page
  const targetPage = document.getElementById('page-' + page);
  if (targetPage) {
    targetPage.classList.add('active');
    // Re-trigger animation
    targetPage.style.animation = 'none';
    targetPage.offsetHeight; // trigger reflow
    targetPage.style.animation = '';
  }

  // Set active nav
  const targetNav = document.querySelector('.nav-item[data-page="' + page + '"]');
  if (targetNav) targetNav.classList.add('active');

  // Update top bar
  const titles = pageTitles[page] || pageTitles.dashboard;
  document.getElementById('page-heading').innerText = titles.heading;
  document.getElementById('page-subtitle').innerText = titles.subtitle;

  // Show/hide refresh button
  document.getElementById('refreshBtn').style.display = (page === 'dashboard') ? '' : 'none';

  // Load data on first visit
  if (page === 'history' && !historyLoaded) {
    loadHistoryData(initialTodayEarn, initialViewToday);
    historyLoaded = true;
  }

  // Load admin data on first visit
  if (page.startsWith('admin-') && !adminLoaded) {
    loadAdminData();
    adminLoaded = true;
  }

  currentPage = page;

  // Close mobile sidebar
  document.getElementById('sidebar').classList.remove('active');
}

// --- CHART JS ---
const ctx = document.getElementById('trafficChart').getContext('2d');
let activityChart;

function initChart(labels, views, earnings) {
  if (activityChart) activityChart.destroy();

  const viewGradient = ctx.createLinearGradient(0, 0, 0, 400);
  viewGradient.addColorStop(0, 'rgba(16, 185, 129, 0.4)'); // Emerald
  viewGradient.addColorStop(0.3, 'rgba(16, 185, 129, 0.1)');
  viewGradient.addColorStop(1, 'rgba(16, 185, 129, 0)');

  const earnGradient = ctx.createLinearGradient(0, 0, 0, 400);
  earnGradient.addColorStop(0, 'rgba(56, 189, 248, 0.4)'); // Sky
  earnGradient.addColorStop(0.3, 'rgba(56, 189, 248, 0.1)');
  earnGradient.addColorStop(1, 'rgba(56, 189, 248, 0)');

  Chart.defaults.font.family = "'Outfit', sans-serif";

  // Shadow Plugin
  const shadowPlugin = {
    id: 'shadowPlugin',
    beforeDraw: (chart) => {
      const { ctx } = chart;
      ctx.save();
      ctx.shadowColor = 'rgba(0, 0, 0, 0.1)';
      ctx.shadowBlur = 10;
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 4;
    },
    afterDraw: (chart) => {
      chart.ctx.restore();
    }
  };

  activityChart = new Chart(ctx, {
    type: 'line',
    plugins: [shadowPlugin],
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Views',
          data: views,
          borderColor: '#10b981',
          backgroundColor: viewGradient,
          borderWidth: 3,
          tension: 0.4,
          fill: true,
          yAxisID: 'y',
          pointRadius: 0,
          pointHoverRadius: 5,
          pointBackgroundColor: '#10b981',
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        },
        {
          label: 'Earnings',
          data: earnings,
          borderColor: '#0ea5e9',
          backgroundColor: earnGradient,
          borderWidth: 3,
          tension: 0.4,
          fill: true,
          yAxisID: 'y1',
          pointRadius: 0,
          pointHoverRadius: 5,
          pointBackgroundColor: '#0ea5e9',
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          align: 'end',
          labels: { boxWidth: 10, usePointStyle: true, font: { size: 12 } }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            label: function (context) {
              let label = context.dataset.label || '';
              if (label === 'Earnings') return label + ': Rp ' + formatNumber(context.parsed.y);
              return label + ': ' + context.parsed.y;
            }
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11 } } },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: { display: true, text: 'Views', font: { weight: '600' } },
          grid: { color: '#f1f5f9', borderDash: [5, 5] },
          ticks: { precision: 0 }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: { display: true, text: 'Earnings (Rp)', font: { weight: '600' } },
          grid: { drawOnChartArea: false },
          ticks: {
            callback: value => 'Rp' + formatNumber(value)
          }
        }
      }
    }
  });
}

function updateStat(id, val, isMoney = false) {
  const el = document.getElementById(id);
  if (!el) return;
  let displayVal = formatNumber(val || 0);
  if (isMoney) displayVal = 'Rp ' + displayVal;
  el.innerText = displayVal;
}

// Utility for numeric formatting in tooltips
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

// Load initial chart data
const chartData = <?!= JSON.stringify(chartData) ?>;

// Initial Earn and Views for Local Fake History
const initialTodayEarn = <?= initialTodayEarn ?>;
const initialViewToday = <?= initialViewToday ?>;

// --- UI FUNCTIONS ---
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('active');
}

function generateShortlink() {
  let url = document.getElementById('urlInput').value.trim();
  const loader = document.getElementById('loading');
  if (!url) return alert("Please enter a URL first.");

  // Validasi URL Strict (mencegah teks asal seperti "hai", tapi mengizinkan parameter & fragment)
  const urlPattern = /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([^\s]*)$/i;
  if (!urlPattern.test(url)) {
    return showToast("URL tidak valid. Harap gunakan format benar (misal: contoh.com)", "error");
  }

  // Tambahkan https:// jika belum ada
  if (!/^https?:\/\//i.test(url)) {
    url = 'https://' + url;
  }

  loader.style.display = 'block';
  document.getElementById('resultCard').style.display = 'none';

  google.script.run
    .withSuccessHandler(res => {
      loader.style.display = 'none';
      if (res.success) {
        document.getElementById('shortlinkResult').innerText = res.shortlink;
        document.getElementById('resultCard').style.display = 'block';
      } else {
        alert(res.message);
      }
    })
    .processShortlinkRequest({ action: 'create', url: url, username: username });
}

function copyToClipboard() {
  const text = document.getElementById('shortlinkResult').innerText;
  navigator.clipboard.writeText(text).then(() => alert("Copied!"));
}

function refreshDashboard() {
  const btn = document.getElementById('refreshBtn');
  const originalHtml = btn.innerHTML;
  btn.innerHTML = '<i class="fas fa-spin fa-sync-alt"></i> Refreshing...';
  btn.disabled = true;

  google.script.run
    .withSuccessHandler(res => {
      btn.innerHTML = originalHtml;
      btn.disabled = false;

      if (!res) return;

      // Update Stats
      updateStat('saldo', res.userData.Saldo, true);
      updateStat('total-view', res.userData.Total_View);
      updateStat('view-today', res.userData.View_Today);
      updateStat('pendapatan-hari-ini', res.userData.Today_Earn, true);
      updateStat('withdraw-pending', res.userData.Withdraw_Pending, true);
      updateStat('withdraw-success', res.userData.Withdraw_Success, true);

      // Update wallet page values too
      updateStat('wallet-saldo', res.userData.Saldo, true);
      updateStat('wallet-pending', res.userData.Withdraw_Pending, true);
      updateStat('wallet-success', res.userData.Withdraw_Success, true);

      // Update status badge
      const statusBadge = document.getElementById('withdraw-status-badge');
      if (statusBadge) {
        const status = res.userData.Status_Penarikan || 'None';
        statusBadge.innerText = 'Status: ' + status;

        if (status === 'Pending') {
          statusBadge.style.background = '#fef3c7';
          statusBadge.style.color = '#b45309';
        } else if (status === 'None') {
          statusBadge.style.background = '#f1f5f9';
          statusBadge.style.color = '#64748b';
        } else {
          statusBadge.style.background = '#d1fae5';
          statusBadge.style.color = '#065f46';
        }
      }

      // Update Chart
      if (res.chartData) {
        initChart(res.chartData.labels, res.chartData.views, res.chartData.earnings);
      }

      // Update Activity & Announcements
      const actType = document.getElementById('activity-type');
      if (actType) actType.innerText = res.userData.Last_Activity_Type || 'Belum ada aktivitas';

      const actDetail = document.getElementById('activity-detail');
      if (actDetail) actDetail.innerText = res.userData.Last_Activity_Detail || 'Aktivitas Anda akan muncul di sini.';

      const annSection = document.getElementById('announcement-section');
      const annText = document.getElementById('announcement-text');
      if (annSection && annText) {
        if (res.userData.Announcement) {
          annSection.style.display = '';
          annText.innerText = res.userData.Announcement;
        } else {
          annSection.style.display = 'none';
        }
      }

      // Update History Table with LOCAL FAKE HISTORY
      loadHistoryData(res.userData.Today_Earn, res.userData.View_Today);

      showToast('Data diperbarui', 'success');
    })
    .withFailureHandler(err => {
      btn.innerHTML = originalHtml;
      btn.disabled = false;
      showToast('Gagal memuat data: ' + err.message, 'error');
    })
    .getDashboardData(username);
}

function logout() {
  CustomAlert.confirm('Logout', 'Apakah Anda yakin ingin keluar?', 'Logout', 'Batal', 'danger')
    .then(res => {
      if (res) {
        localStorage.removeItem('kliqify_username');
        localStorage.removeItem('kliqify_password');
        window.top.location.href = appUrl;
      }
    });
}

// --- WALLET: WITHDRAWAL ---
function submitWithdrawal(e) {
  e.preventDefault();

  const btn = document.getElementById('withdrawBtn');
  const originalText = btn.innerHTML;

  const amount = document.getElementById('amount').value;
  const method = document.getElementById('method').value;
  const accountNumber = document.getElementById('accountNumber').value;

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Memproses...';

  google.script.run
    .withSuccessHandler(res => {
      btn.disabled = false;
      btn.innerHTML = originalText;
      if (res.success) {
        showToast(res.message, 'success');
        document.getElementById('withdrawalForm').reset();
        refreshDashboard(); // Update balance UI immediately
      } else {
        showToast(res.message, 'error');
      }
    })
    .withFailureHandler(err => {
      btn.disabled = false;
      btn.innerHTML = originalText;
      showToast('Terjadi kesalahan sistem: ' + (err.message || err), 'error');
    })
    .processWithdrawal({
      username: username,
      amount: amount,
      method: method,
      accountNumber: accountNumber
    });
}

// --- LOCAL FAKE HISTORY GENERATOR ---
function generateLocalHistory(earn, views, username) {
  if (!username) return [];

  const dateStr = new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD
  const storageKey = `kliqify_history_${username}_${dateStr}`;

  let localData = JSON.parse(localStorage.getItem(storageKey) || '{"earn":0,"views":0,"history":[]}');

  let earnDiff = earn - localData.earn;
  let viewsDiff = views - localData.views;

  // Handle server reset or new day
  if (earn < localData.earn || views < localData.views) {
    localData = { earn: 0, views: 0, history: [] };
    earnDiff = earn;
    viewsDiff = views;
  }

  if (earnDiff > 0 || viewsDiff > 0) {
    // Randomly split the difference into 1 to 3 transactions
    const numSplits = (earnDiff > 0 || viewsDiff > 0) ? Math.floor(Math.random() * 3) + 1 : 0;
    let remainingEarn = earnDiff;
    let remainingViews = viewsDiff;

    for (let i = 0; i < numSplits; i++) {
      let splitEarn, splitViews;
      if (i === numSplits - 1) {
        splitEarn = remainingEarn;
        splitViews = remainingViews;
      } else {
        // Take a random fraction (20% to 80%) of the remaining amount
        const fractionE = 0.2 + Math.random() * 0.6;
        const fractionV = 0.2 + Math.random() * 0.6;
        splitEarn = Math.floor(remainingEarn * fractionE);
        splitViews = Math.floor(remainingViews * fractionV);
        remainingEarn -= splitEarn;
        remainingViews -= splitViews;
      }

      if (splitEarn > 0 || splitViews > 0) {
        // Generate a random time within the last 30 minutes
        const now = new Date();
        now.setMinutes(now.getMinutes() - Math.floor(Math.random() * 30));
        const timeStr = now.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) + ' ' +
          now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');

        localData.history.unshift({
          timestamp: timeStr,
          source: 'Shortlink Views',
          views: splitViews,
          amount: splitEarn
        });
      }
    }

    localData.earn = earn;
    localData.views = views;

    if (localData.history.length > 50) {
      localData.history = localData.history.slice(0, 50);
    }

    localStorage.setItem(storageKey, JSON.stringify(localData));
  }

  return localData.history;
}

// --- HISTORY ---
function switchHistoryTab(tab) {
  document.querySelectorAll('.history-tab').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.history-content').forEach(el => el.classList.remove('active'));


  event.currentTarget.classList.add('active');
  document.getElementById('history-' + tab).classList.add('active');
}

function loadHistoryData(earnAmount, viewCount) {
  // Load withdrawal history
  google.script.run
    .withSuccessHandler(res => {
      const tbody = document.getElementById('history-penarikan-body');
      if (!res || !res.length) {
        tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><i class="fas fa-inbox"></i><p>Belum ada riwayat penarikan</p></div></td></tr>';
        return;
      }

      tbody.innerHTML = res.map(item => {
        const statusClass = item.status.toLowerCase() === 'pending' ? 'pending' :
          (item.status.toLowerCase() === 'success' || item.status.toLowerCase() === 'berhasil' || item.status.toLowerCase() === 'approved') ? 'success' : 'rejected';
        return `<tr>
              <td>${item.timestamp}</td>
              <td>Rp ${formatNumber(item.amount)}</td>
              <td>${item.method}</td>
              <td>${item.account}</td>
              <td><span class="status-badge ${statusClass}">${item.status}</span></td>
            </tr>`;
      }).join('');
    })
    .withFailureHandler(err => {
      document.getElementById('history-penarikan-body').innerHTML =
        '<tr><td colspan="5"><div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Gagal memuat data: ' + err.message + '</p></div></td></tr>';
    })
    .getWithdrawalHistory(username);

  // Populate pendapatan from LOCAL FAKE HISTORY
  const pendapatanBody = document.getElementById('history-pendapatan-body');

  // Handle the initial page load where earnAmount might be undefined in some cases
  const finalEarn = typeof earnAmount !== 'undefined' ? earnAmount : (typeof initialTodayEarn !== 'undefined' ? initialTodayEarn : 0);
  const finalViews = typeof viewCount !== 'undefined' ? viewCount : (typeof initialViewToday !== 'undefined' ? initialViewToday : 0);

  const localHistoryData = generateLocalHistory(finalEarn, finalViews, username);

  if (localHistoryData && localHistoryData.length > 0) {
    let rows = '';
    localHistoryData.forEach(item => {
      rows += `<tr>
              <td>${item.timestamp}</td>
              <td>${item.source}</td>
              <td>${item.views}</td>
              <td style="color: var(--primary); font-weight: 600;">Rp ${formatNumber(item.amount)}</td>
            </tr>`;
    });
    pendapatanBody.innerHTML = rows;
  } else {
    pendapatanBody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><i class="fas fa-inbox"></i><p>Belum ada riwayat pendapatan</p></div></td></tr>';
  }
}

// --- SETTINGS ---
function updateName(e) {
  e.preventDefault();
  const btn = document.getElementById('updateNameBtn');
  const originalText = btn.innerHTML;
  const newName = document.getElementById('newName').value.trim();

  if (!newName || newName.length < 2) {
    showToast('Nama minimal 2 karakter', 'error');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Menyimpan...';

  google.script.run
    .withSuccessHandler(res => {
      btn.disabled = false;
      btn.innerHTML = originalText;
      if (res.success) {
        showToast(res.message, 'success');
        // Update UI
        document.getElementById('current-name-display').innerText = newName;
        document.getElementById('page-subtitle').innerText = 'Pengaturan akun Anda';
        pageTitles.dashboard.subtitle = 'Welcome back, ' + newName;
        document.getElementById('newName').value = '';
      } else {
        showToast(res.message, 'error');
      }
    })
    .withFailureHandler(err => {
      btn.disabled = false;
      btn.innerHTML = originalText;
      showToast('Terjadi kesalahan: ' + (err.message || err), 'error');
    })
    .updateUserName({ username: username, newName: newName });
}

function updatePassword(e) {
  e.preventDefault();
  const btn = document.getElementById('updatePassBtn');
  const originalText = btn.innerHTML;

  const oldPassword = document.getElementById('oldPassword').value;
  const newPassword = document.getElementById('newPassword').value;
  const confirmPassword = document.getElementById('confirmPassword').value;

  if (newPassword.length < 4) {
    showToast('Password baru minimal 4 karakter', 'error');
    return;
  }

  if (newPassword !== confirmPassword) {
    showToast('Password baru dan konfirmasi tidak cocok!', 'error');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Mengubah...';

  google.script.run
    .withSuccessHandler(res => {
      btn.disabled = false;
      btn.innerHTML = originalText;
      if (res.success) {
        showToast(res.message, 'success');
        document.getElementById('oldPassword').value = '';
        document.getElementById('newPassword').value = '';
        document.getElementById('confirmPassword').value = '';
      } else {
        showToast(res.message, 'error');
      }
    })
    .withFailureHandler(err => {
      btn.disabled = false;
      btn.innerHTML = originalText;
      showToast('Terjadi kesalahan: ' + (err.message || err), 'error');
    })
    .updateUserPassword({ username: username, oldPassword: oldPassword, newPassword: newPassword });
}

// --- INITIALIZATION ---
window.addEventListener('load', () => {
  if (isAdmin) {
    document.querySelectorAll('.user-only').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'flex');

    // Admin initial load
    navigateTo('admin-dashboard');
  } else {
    document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.user-only').forEach(el => el.style.display = 'flex');

    initChart(chartData.labels, chartData.views, chartData.earnings);
    loadHistoryData(initialTodayEarn, initialViewToday);
    historyLoaded = true;
    navigateTo('dashboard');
    if (username) {
      refreshDashboard();
    }
  }
});


