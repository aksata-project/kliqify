const fs = require('fs');

function refactorDashboard() {
    let content = fs.readFileSync('dashboard.html', 'utf-8');

    // Make sure we have the nav updated
    console.log("Checking navigation...");
    if (!content.includes('data-page="admin-dashboard"')) {
        const navPattern = /<div class="nav-item(?:\s+admin-only)?" data-page="admin"[^>]*>.*?<\/div>/s;
        const newNav = `      <div class="nav-section-title admin-only" style="display: none; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); font-weight: 700; margin: 20px 20px 8px;">
        Admin Panel
      </div>
      <div class="nav-item admin-only" data-page="admin-dashboard" onclick="navigateTo('admin-dashboard')" style="display: none;">
        <i class="fas fa-chart-line" style="color: var(--primary);"></i> Statistik
      </div>
      <div class="nav-item admin-only" data-page="admin-users" onclick="navigateTo('admin-users')" style="display: none;">
        <i class="fas fa-users" style="color: #38bdf8;"></i> Kelola Pengguna
      </div>
      <div class="nav-item admin-only" data-page="admin-withdraws" onclick="navigateTo('admin-withdraws')" style="display: none;">
        <i class="fas fa-money-check-alt" style="color: #10b981;"></i> Kelola Penarikan
      </div>`;
        content = content.replace(navPattern, newNav);
        console.log("Updated Sidebar Admin Navigation.");
    }

    // Split Admin Pages
    console.log("Splitting Admin Pages...");
    const adminPageRegex = /<div class="page-section admin-only" id="page-admin"[^>]*>([\s\S]*?)<\/div>\s*<\/div>\s*<\/main>/;
    const adminMatch = content.match(adminPageRegex);

    if (adminMatch) {
        let adminContent = adminMatch[1];
        const usersMatch = adminContent.match(/(<div class="card"[^>]*>\s*<div[^>]*>\s*<h3[^>]*>Daftar Pengguna<\/h3>)/);

        if (usersMatch) {
            let part1_dashboard = adminContent.substring(0, usersMatch.index);
            let restContent = adminContent.substring(usersMatch.index);

            const withdrawMatch = restContent.match(/(<div class="card"[^>]*>\s*<div[^>]*>\s*<h3[^>]*>Menunggu Persetujuan Penarikan \(Pending\)<\/h3>)/);

            if (withdrawMatch) {
                let part2_users = restContent.substring(0, withdrawMatch.index);
                let part3_withdraws = restContent.substring(withdrawMatch.index);

                const newAdminHtml = `
      <!-- ========== PAGE: ADMIN DASHBOARD ========== -->
      <div class="page-section admin-only" id="page-admin-dashboard" style="display:none;">
        <div class="hero-card" style="margin-bottom: 24px; padding: 24px; background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);">
          <i class="fas fa-shield-alt hero-bg-icon"></i>
          <div class="hero-content">
            <h2 style="font-size: 24px; margin-bottom: 8px;">Admin Dashboard</h2>
            <p style="opacity: 0.9; font-size: 15px;">Pantau performa sistem dan kelola operasi global.</p>
          </div>
        </div>
${part1_dashboard}
      </div>

      <!-- ========== PAGE: ADMIN USERS ========== -->
      <div class="page-section admin-only" id="page-admin-users" style="display:none;">
        <div class="hero-card" style="margin-bottom: 24px; padding: 20px 24px; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); border-radius: 16px;">
          <h2 style="font-size: 20px; margin:0;"><i class="fas fa-users" style="margin-right:8px;"></i> Kelola Pengguna</h2>
        </div>
${part2_users}
      </div>

      <!-- ========== PAGE: ADMIN WITHDRAWS ========== -->
      <div class="page-section admin-only" id="page-admin-withdraws" style="display:none;">
        <div class="hero-card" style="margin-bottom: 24px; padding: 20px 24px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 16px;">
          <h2 style="font-size: 20px; margin:0;"><i class="fas fa-money-check-alt" style="margin-right:8px;"></i> Kelola Penarikan</h2>
        </div>
${part3_withdraws}
      </div>
`;
                const fullReplacement = newAdminHtml + "\n    </div>\n  </main>";
                content = content.replace(adminMatch[0], fullReplacement);
                console.log("Successfully split admin block into 3 pages!");
            } else {
                console.log("Could not find 'Menunggu Persetujuan Penarikan' card to split Withdrawals.");
            }
        } else {
            console.log("Could not find 'Daftar Pengguna' card to split Users.");
        }
    } else {
        console.log("Admin page already split or could not find 'page-admin' master container.");
    }

    fs.writeFileSync('dashboard.html', content, 'utf-8');
    console.log("Saved 'dashboard.html'.");
}

refactorDashboard();
