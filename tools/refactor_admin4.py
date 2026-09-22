import os
import re

def refactor_dashboard():
    with open('dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # --- 1. Fix CSS for Grid and Table Responsiveness ---
    print("Updating CSS Grid & Mobile Responsiveness...")
    
    # We add detailed CSS for table scroll and better grids if not already present
    responsive_css = """
    /* -- Responsive Grids & Tables -- */
    .admin-table-responsive {
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      margin-bottom: 1rem;
      border-radius: var(--radius-md);
      box-shadow: inset 0 0 0 1px var(--border);
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }
    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 24px;
      margin-bottom: 24px;
    }
    @media (max-width: 768px) {
      .stats-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
      }
      .admin-table th, .admin-table td {
        white-space: nowrap;
        font-size: 13px;
        padding: 10px;
      }
    }
    @media (max-width: 480px) {
      .stats-grid {
        grid-template-columns: 1fr;
      }
    }
"""
    # Simply inject before </style> if we don't already have `.admin-table-responsive {` block with overflow-x
    if '-webkit-overflow-scrolling: touch;' not in content:
        content = content.replace('</style>', responsive_css + '\n</style>', 1)
        print("Injected Responsive CSS.")

    
    # --- 2. Fix the Navigation (If missing) ---
    print("Checking navigation...")
    if 'data-page="admin-dashboard"' not in content:
        # User might still have the old data-page="admin" 
        nav_pattern = r'<div class="nav-item(?:\s+admin-only)?" data-page="admin"[^>]*>.*?</div>'
        new_nav = """      <div class="nav-section-title admin-only" style="display: none; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); font-weight: 700; margin: 20px 20px 8px;">
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
      </div>"""
        content = re.sub(nav_pattern, new_nav, content, flags=re.DOTALL)
        print("Updated Sidebar Admin Navigation.")
    else:
        print("Sidebar Navigation already split.")

    
    # --- 3. Split the Admin Page ---
    print("Splitting Admin Pages...")
    # Find the big admin page block
    admin_page_match = re.search(r'<div class="page-section admin-only" id="page-admin"[^>]*>(.*?)</div>\s*</div>\s*</main>', content, re.DOTALL)
    
    if admin_page_match:
        admin_content = admin_page_match.group(1)
        
        # We need to split admin_content into 3 parts: Dashboard, Users, Withdraws.
        # Dashboard is everything before "Daftar Pengguna"
        # Users is from "Daftar Pengguna" card to "Menunggu Persetujuan Penarikan" card
        # Withdraws is from "Menunggu Persetujuan Penarikan" card to the end.
        
        # Split 1: Dashboard vs Rest
        # Find the card containing "Daftar Pengguna"
        users_split_match = re.search(r'(<div class="card"[^>]*>\s*<div[^>]*>\s*<h3[^>]*>Daftar Pengguna</h3>)', admin_content)
        
        if users_split_match:
            part1_dashboard = admin_content[:users_split_match.start(1)]
            rest_content = admin_content[users_split_match.start(1):]
            
            # Split 2: Users vs Withdraws
            # Find the card containing "Menunggu Persetujuan Penarikan (Pending)"
            withdraw_split_match = re.search(r'(<div class="card"[^>]*>\s*<div[^>]*>\s*<h3[^>]*>Menunggu Persetujuan Penarikan \(Pending\)</h3>)', rest_content)
            
            if withdraw_split_match:
                part2_users = rest_content[:withdraw_split_match.start(1)]
                part3_withdraws = rest_content[withdraw_split_match.start(1):]
                
                # Wrap each part in its new page-section container
                new_admin_html = f"""
      <!-- ========== PAGE: ADMIN DASHBOARD ========== -->
      <div class="page-section admin-only" id="page-admin-dashboard" style="display:none;">
        <div class="hero-card" style="margin-bottom: 24px; padding: 24px; background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);">
          <i class="fas fa-shield-alt hero-bg-icon"></i>
          <div class="hero-content">
            <h2 style="font-size: 24px; margin-bottom: 8px;">Admin Dashboard</h2>
            <p style="opacity: 0.9; font-size: 15px;">Pantau performa sistem dan kelola operasi global.</p>
          </div>
        </div>
{part1_dashboard}
      </div>

      <!-- ========== PAGE: ADMIN USERS ========== -->
      <div class="page-section admin-only" id="page-admin-users" style="display:none;">
        <div class="hero-card" style="margin-bottom: 24px; padding: 20px 24px; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); border-radius: 16px;">
          <h2 style="font-size: 20px; margin:0;"><i class="fas fa-users" style="margin-right:8px;"></i> Kelola Pengguna</h2>
        </div>
{part2_users}
      </div>

      <!-- ========== PAGE: ADMIN WITHDRAWS ========== -->
      <div class="page-section admin-only" id="page-admin-withdraws" style="display:none;">
        <div class="hero-card" style="margin-bottom: 24px; padding: 20px 24px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 16px;">
          <h2 style="font-size: 20px; margin:0;"><i class="fas fa-money-check-alt" style="margin-right:8px;"></i> Kelola Penarikan</h2>
        </div>
{part3_withdraws}
      </div>
"""
                # Replace the original page-admin block
                original_block = admin_page_match.group(0)
                # Need to add back the closing tags we captured in the regex
                replacement = new_admin_html + "\n    </div>\n  </main>"
                content = content.replace(original_block, replacement)
                print("Successfully split admin block into 3 pages!")
            else:
                print("Could not find 'Menunggu Persetujuan Penarikan' card to split Withdrawals.")
        else:
            print("Could not find 'Daftar Pengguna' card to split Users.")
    else:
        print("Admin page already split or could not find 'page-admin' master container.")

    
    # Save the file
    with open('dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Saved 'dashboard.html'.")

if __name__ == "__main__":
    refactor_dashboard()
