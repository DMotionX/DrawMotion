import os
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QUrl, QSize, QEvent
from PySide6.QtGui import QDesktopServices
from utils.theme import THEME_COLORS
from utils.icons import get_icon
from core.updater import UpdateCheckerThread, CURRENT_VERSION
from core.update_engine.ui import FastUpdateDialog
from .project_settings import SettingsSection, divider

# Official & Social Links configuration (extensible for future accounts)
OFFICIAL_LINKS = [
    {
        "title": "X / Twitter",
        "subtitle": "@MohamedFad19757",
        "icon": "x_twitter",
        "url": "https://x.com/MohamedFad19757"
    },
    {
        "title": "GitHub",
        "subtitle": "MohamedFadl2344",
        "icon": "github",
        "url": "https://github.com/MohamedFadl2344"
    },
    {
        "title": "Facebook",
        "subtitle": "EASY SOFT Team Official",
        "icon": "facebook",
        "url": "https://www.facebook.com/profile.php?id=61592234934862&locale=ar_AR"
    },
    {
        "title": "Official Website",
        "subtitle": "drawmotion-web.vercel.app",
        "icon": "globe",
        "url": "https://drawmotion-web.vercel.app/"
    },
    {
        "title": "Team X / Twitter",
        "subtitle": "Coming Soon",
        "icon": "x_twitter",
        "url": None  # Future slot: active once URL is set
    },
    {
        "title": "Team Instagram",
        "subtitle": "Coming Soon",
        "icon": "globe",
        "url": None  # Future slot: active once URL is set
    }
]

class UpdateSettings(SettingsSection):
    """
    Comprehensive System & Updates Hub (v2).
    Features: Card-based architecture, zero black background strips,
    rich interactive social tiles, and error-free QSS styling.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.updater = UpdateCheckerThread()
        self._latest_version_info = None
        self._setup_ui()

    def eventFilter(self, obj, event):
        """Safe event filter for social tiles replacing lambda mousePressEvent."""
        if event.type() == QEvent.Type.MouseButtonPress:
            url = obj.property("link_url")
            if url:
                QDesktopServices.openUrl(QUrl(url))
                return True
        return super().eventFilter(obj, event)

    def _on_rollback_clicked(self):
        if hasattr(self, '_prev_rollback_info'):
            prev_ver, prev_inst = self._prev_rollback_info
            self._handle_rollback_action(prev_ver, prev_inst)

    def _setup_ui(self):
        # ── Card 1: Software & Version Status ────────────────────────────────
        card1 = self.begin_card("Software & Updates")
        
        # Header Row: App Name + Version & Channel Badges
        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        
        app_title = QLabel("DrawMotion Studio")
        app_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF; background: transparent;")
        header_row.addWidget(app_title)
        
        ver_badge = QLabel(f"v{CURRENT_VERSION}")
        ver_badge.setStyleSheet(f"""
            background-color: {THEME_COLORS['primary_green']}25;
            color: {THEME_COLORS['primary_green']};
            border: 1px solid {THEME_COLORS['primary_green']};
            border-radius: 5px;
            padding: 3px 10px;
            font-size: 12px;
            font-weight: bold;
        """)
        header_row.addWidget(ver_badge)
        
        channel_badge = QLabel("Stable Release")
        channel_badge.setStyleSheet(f"""
            background-color: #111D18;
            color: {THEME_COLORS['text_secondary']};
            border: 1px solid #25382F;
            border-radius: 5px;
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 500;
        """)
        header_row.addWidget(channel_badge)
        header_row.addStretch()
        card1.addLayout(header_row)

        # Status Banner Container (No black boxes, soft glowing container)
        self.status_banner = QFrame()
        self.status_banner.setObjectName("status_banner")
        self.status_banner.setStyleSheet("""
            QFrame#status_banner {
                background-color: #14231D;
                border: 1px solid #223D31;
                border-radius: 10px;
            }
        """)
        banner_layout = QHBoxLayout(self.status_banner)
        banner_layout.setContentsMargins(16, 12, 16, 12)
        banner_layout.setSpacing(14)
        
        self.status_icon = QLabel()
        self.status_icon.setStyleSheet("background: transparent; border: none;")
        self.status_icon.setPixmap(get_icon("check_circle", "#3FA36D").pixmap(24, 24))
        banner_layout.addWidget(self.status_icon)
        
        status_text_layout = QVBoxLayout()
        status_text_layout.setSpacing(3)
        
        self.status_title = QLabel("System Up to Date")
        self.status_title.setStyleSheet("color: #3FA36D; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        status_text_layout.addWidget(self.status_title)
        
        self.status_desc = QLabel(f"DrawMotion Studio is running the latest stable build (v{CURRENT_VERSION}) • Checked today")
        self.status_desc.setStyleSheet("color: #7A9E90; font-size: 12px; background: transparent; border: none;")
        status_text_layout.addWidget(self.status_desc)
        
        banner_layout.addLayout(status_text_layout)
        banner_layout.addStretch()
        card1.addWidget(self.status_banner)
        
        # Progress Bar (Hidden during idle)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #111D18;
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {THEME_COLORS['primary_green']};
                border-radius: 3px;
            }}
        """)
        card1.addWidget(self.progress_bar)

        # Action Buttons Row
        action_row = QHBoxLayout()
        action_row.setSpacing(12)
        
        self.check_btn = QPushButton("Check for Updates")
        self.check_btn.setIcon(get_icon("update", "white"))
        self.check_btn.setIconSize(QSize(16, 16))
        self.check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_btn.setFixedSize(200, 42)
        self.check_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['primary_green']};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                border-radius: 8px;
                border: none;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: {THEME_COLORS['green_hover']};
            }}
        """)
        self.check_btn.clicked.connect(self._check_updates)
        action_row.addWidget(self.check_btn)
        
        self.whats_new_btn = QPushButton(f"Release Notes (v{CURRENT_VERSION})")
        self.whats_new_btn.setIcon(get_icon("preview", "#D0D8D4"))
        self.whats_new_btn.setIconSize(QSize(16, 16))
        self.whats_new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.whats_new_btn.setFixedSize(200, 42)
        self.whats_new_btn.setStyleSheet("""
            QPushButton {{
                background-color: #13221C;
                border: 1px solid #284437;
                border-radius: 8px;
                color: #D0D8D4;
                font-size: 13px;
                font-weight: 500;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: #1B2F26;
                border-color: #3FA36D;
                color: #FFFFFF;
            }}
        """)
        self.whats_new_btn.clicked.connect(self._show_whats_new)
        action_row.addWidget(self.whats_new_btn)

        # Rollback Button (Available if a previous installer exists in vault)
        from core.recovery_engine.watchdog import get_previous_installer_info
        prev_ver, prev_inst = get_previous_installer_info()
        if prev_ver and prev_inst:
            self.rollback_btn = QPushButton(f"Rollback to v{prev_ver}")
            self.rollback_btn.setIcon(get_icon("download", "#E57373"))
            self.rollback_btn.setIconSize(QSize(16, 16))
            self.rollback_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.rollback_btn.setFixedSize(180, 42)
            self.rollback_btn.setStyleSheet("""
                QPushButton {
                    background-color: #241513;
                    border: 1px solid #4D2622;
                    border-radius: 8px;
                    color: #E57373;
                    font-size: 13px;
                    font-weight: 500;
                    padding: 0 14px;
                }
                QPushButton:hover {
                    background-color: #381E1B;
                    border-color: #E57373;
                    color: #FFFFFF;
                }
            """)
            self._prev_rollback_info = (prev_ver, prev_inst)
            self.rollback_btn.clicked.connect(self._on_rollback_clicked)
            action_row.addWidget(self.rollback_btn)

        action_row.addStretch()
        card1.addLayout(action_row)

        # ── Card 2: Creators & Leadership (EASY SOFT) ───────────────────────
        card2 = self.begin_card("About EASY SOFT & Authors")
        
        team_title = QLabel("EASY SOFT Team")
        team_title.setStyleSheet("color: #3FA36D; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        card2.addWidget(team_title)
        
        # Mission Quote Box
        mission_box = QFrame()
        mission_box.setStyleSheet("""
            QFrame {
                background-color: #121D18;
                border: 1px solid #1E2E26;
                border-left: 3px solid #2E8B57;
                border-radius: 6px;
            }
        """)
        mission_layout = QVBoxLayout(mission_box)
        mission_layout.setContentsMargins(14, 10, 14, 10)
        
        mission_desc = QLabel(
            "An independent non-profit software team fighting digital monopolies by engineering "
            "high-speed, local-first vector animation software that respects user privacy and sovereignty."
        )
        mission_desc.setWordWrap(True)
        mission_desc.setStyleSheet("color: #A6ABA8; font-size: 12px; line-height: 1.4; background: transparent; border: none;")
        mission_layout.addWidget(mission_desc)
        card2.addWidget(mission_box)
        
        # Creators Tiles Row
        creators_row = QHBoxLayout()
        creators_row.setSpacing(14)
        
        # Founder Tile
        founder_tile = QFrame()
        founder_tile.setStyleSheet("""
            QFrame {
                background-color: #13211B;
                border: 1px solid #22362C;
                border-radius: 8px;
            }
        """)
        founder_layout = QVBoxLayout(founder_tile)
        founder_layout.setContentsMargins(16, 12, 16, 12)
        founder_layout.setSpacing(3)
        
        founder_lbl = QLabel("FOUNDER & SOLE LEAD ENGINEER")
        founder_lbl.setStyleSheet("color: #7A9E90; font-size: 10px; font-weight: bold; background: transparent; border: none;")
        founder_val = QLabel("Mohamed Fadl")
        founder_val.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        founder_layout.addWidget(founder_lbl)
        founder_layout.addWidget(founder_val)
        creators_row.addWidget(founder_tile)
        
        # Community Tile
        community_tile = QFrame()
        community_tile.setStyleSheet("""
            QFrame {
                background-color: #13211B;
                border: 1px solid #22362C;
                border-radius: 8px;
            }
        """)
        community_layout = QVBoxLayout(community_tile)
        community_layout.setContentsMargins(16, 12, 16, 12)
        community_layout.setSpacing(3)
        
        community_lbl = QLabel("CONTRIBUTING COMMUNITY")
        community_lbl.setStyleSheet("color: #7A9E90; font-size: 10px; font-weight: bold; background: transparent; border: none;")
        community_val = QLabel("Beta Testers & Open Contributors")
        community_val.setStyleSheet("color: #D0D8D4; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        community_layout.addWidget(community_lbl)
        community_layout.addWidget(community_val)
        creators_row.addWidget(community_tile)
        
        card2.addLayout(creators_row)

        # ── Card 3: Official Ecosystem & Social Hub ────────────────────────
        card3 = self.begin_card("Official Links & Community Hub")
        
        links_intro = QLabel("Connect with official channels, explore public releases, and join the community:")
        links_intro.setStyleSheet("color: #7A9E90; font-size: 12px; background: transparent; border: none;")
        card3.addWidget(links_intro)
        
        # 2-Column Grid of Rich Social Tiles
        links_grid = QVBoxLayout()
        links_grid.setSpacing(12)
        
        for i in range(0, len(OFFICIAL_LINKS), 2):
            row = QHBoxLayout()
            row.setSpacing(12)
            
            tile1 = self._create_social_tile(OFFICIAL_LINKS[i])
            row.addWidget(tile1)
            
            if i + 1 < len(OFFICIAL_LINKS):
                tile2 = self._create_social_tile(OFFICIAL_LINKS[i + 1])
                row.addWidget(tile2)
            else:
                row.addStretch()
            links_grid.addLayout(row)
            
        card3.addLayout(links_grid)
        card3.addWidget(divider())
        
        # Legal Policies & EULA Footer Row
        legal_row = QHBoxLayout()
        legal_btn = QPushButton("Read Legal Policies & EULA")
        legal_btn.setIcon(get_icon("shield", THEME_COLORS['primary_green']))
        legal_btn.setIconSize(QSize(16, 16))
        legal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        legal_btn.setFixedHeight(36)
        legal_btn.setStyleSheet("""
            QPushButton {{
                background-color: #121E19;
                border: 1px solid #243B30;
                border-radius: 6px;
                color: #D0D8D4;
                font-size: 12px;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: #182B22;
                border-color: #3FA36D;
                color: #FFFFFF;
            }}
        """)
        legal_btn.clicked.connect(self._open_legal_policies)
        legal_row.addWidget(legal_btn)
        
        # Engine Integrity Badge
        engine_badge = QLabel("Engine: 100% Local Processing • Rust Native Security Active")
        engine_badge.setStyleSheet("color: #4A6055; font-size: 11px; background: transparent; border: none;")
        legal_row.addStretch()
        legal_row.addWidget(engine_badge)
        card3.addLayout(legal_row)

        # ── Connections ──────────────────────────────────────────────────────
        self.updater.update_available.connect(self._on_update_found)
        self.updater.no_update.connect(self._on_update_not_found)
        self.updater.error.connect(self._on_error)

    def _create_social_tile(self, link_info: dict) -> QFrame:
        """
        Creates a rich two-line interactive social tile.
        Features prominent icons, clear typography, and robust styling without QSS parse errors.
        """
        tile = QFrame()
        tile.setFixedHeight(56)
        
        title = link_info["title"]
        subtitle = link_info["subtitle"]
        icon_name = link_info["icon"]
        url = link_info.get("url")
        is_active = bool(url)
        
        if is_active:
            tile.setObjectName("active_tile")
            tile.setCursor(Qt.CursorShape.PointingHandCursor)
            tile.setStyleSheet("""
                QFrame#active_tile {
                    background-color: #111D18;
                    border: 1px solid #23372E;
                    border-radius: 10px;
                }
                QFrame#active_tile:hover {
                    background-color: #172A21;
                    border: 1px solid #3FA36D;
                }
            """)
            # Click handler on the frame
            tile.setProperty("link_url", url)
            tile.installEventFilter(self)
        else:
            tile.setObjectName("disabled_tile")
            tile.setStyleSheet("""
                QFrame#disabled_tile {
                    background-color: #0E1613;
                    border: 1px dashed #1C2A24;
                    border-radius: 10px;
                }
            """)
            
        layout = QHBoxLayout(tile)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)
        
        # Icon (bright white or green if active, muted if disabled)
        icon_lbl = QLabel()
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        icon_color = "#3FA36D" if is_active else "#3D5248"
        icon_lbl.setPixmap(get_icon(icon_name, icon_color).pixmap(20, 20))
        layout.addWidget(icon_lbl)
        
        # Two-line text block
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            font-size: 13px;
            font-weight: bold;
            color: {'#FFFFFF' if is_active else '#5A7065'};
            background: transparent;
            border: none;
        """)
        text_layout.addWidget(title_lbl)
        
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(f"""
            font-size: 11px;
            color: {'#7A9E90' if is_active else '#405249'};
            background: transparent;
            border: none;
        """)
        text_layout.addWidget(sub_lbl)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Right badge or arrow
        if is_active:
            arrow_lbl = QLabel()
            arrow_lbl.setStyleSheet("background: transparent; border: none;")
            arrow_lbl.setPixmap(get_icon("external_link", "#7A9E90").pixmap(14, 14))
            layout.addWidget(arrow_lbl)
        else:
            badge_lbl = QLabel("Coming Soon")
            badge_lbl.setStyleSheet("""
                background-color: #13201A;
                color: #556B60;
                font-size: 10px;
                font-weight: bold;
                border-radius: 4px;
                padding: 2px 7px;
                border: 1px solid #1E2D26;
            """)
            layout.addWidget(badge_lbl)
            
        return tile

    def _check_updates(self):
        if self._latest_version_info and self.check_btn.text() == "Update Available":
            dialog = FastUpdateDialog(self._latest_version_info, self)
            dialog.exec()
            return

        self.check_btn.setEnabled(False)
        self.check_btn.setText("Checking...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_title.setText("Connecting...")
        self.status_title.setStyleSheet("color: #A6ABA8; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        self.status_desc.setText("Querying GitHub release servers for updates...")
        self.status_icon.setPixmap(get_icon("update", THEME_COLORS['text_secondary']).pixmap(24, 24))
        self.updater.start()

    def _on_update_found(self, version_info):
        self._latest_version_info = version_info
        self.progress_bar.setVisible(False)
        self.status_title.setText(f"Update Available: v{version_info['version']}")
        self.status_title.setStyleSheet("color: #F28C28; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        self.status_desc.setText(f"A new version of DrawMotion Studio is ready to install • Checked today at {time.strftime('%I:%M %p')}")
        self.status_icon.setPixmap(get_icon("download", THEME_COLORS['orange_action']).pixmap(24, 24))
        self.status_banner.setStyleSheet("""
            QFrame#status_banner {
                background-color: #261D14;
                border: 1px solid #4D331C;
                border-radius: 10px;
            }
        """)
        self.check_btn.setText("Update Available")
        self.check_btn.setIcon(get_icon("download", "white"))
        self.check_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['orange_action']};
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 8px;
                border: none;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {THEME_COLORS['orange_hover']};
            }}
        """)
        self.check_btn.setEnabled(True)
        
        dialog = FastUpdateDialog(version_info, self)
        dialog.exec()

    def _on_update_not_found(self):
        self.progress_bar.setVisible(False)
        self.status_title.setText("System Up to Date")
        self.status_title.setStyleSheet("color: #3FA36D; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        self.status_desc.setText(f"DrawMotion Studio is running the latest stable build (v{CURRENT_VERSION}) • Checked today at {time.strftime('%I:%M %p')}")
        self.status_icon.setPixmap(get_icon("check_circle", "#3FA36D").pixmap(24, 24))
        self.status_banner.setStyleSheet("""
            QFrame#status_banner {
                background-color: #14231D;
                border: 1px solid #223D31;
                border-radius: 10px;
            }
        """)
        self.check_btn.setText("Check for Updates")
        self.check_btn.setIcon(get_icon("update", "white"))
        self.check_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['primary_green']};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                border-radius: 8px;
                border: none;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {THEME_COLORS['green_hover']};
            }}
        """)
        self.check_btn.setEnabled(True)
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Up to Date")
        msg.setText("DrawMotion Studio is fully up to date.")
        msg.setInformativeText(f"You are running the latest version (v{CURRENT_VERSION}).")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet(f"background-color: {THEME_COLORS['bg_secondary']}; color: {THEME_COLORS['text_primary']};")
        msg.exec()

    def _on_error(self, message):
        self.progress_bar.setVisible(False)
        self.status_title.setText("Check Failed")
        self.status_title.setStyleSheet("color: #E57373; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        self.status_desc.setText(f"Could not connect to update servers: {message}")
        self.check_btn.setText("Retry Check")
        self.check_btn.setEnabled(True)

    def _show_whats_new(self):
        """Displays current release highlights in the polished scrollable dialog."""
        changelog_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "CHANGELOG.md")
        changelog_text = ""
        if os.path.exists(changelog_path):
            try:
                with open(changelog_path, "r", encoding="utf-8") as f:
                    changelog_text = f.read()
            except Exception:
                pass
                
        if not changelog_text:
            changelog_text = (
                f"### DrawMotion Studio v{CURRENT_VERSION}\n\n"
                "- Full offline local-first vector animation.\n"
                "- High-speed parallel update engine.\n"
                "- Pure C++ & Rust hardware-assisted architecture."
            )
            
        dialog = FastUpdateDialog({
            "version": CURRENT_VERSION,
            "changelog": changelog_text,
            "url": ""
        }, self)
        dialog.update_btn.setVisible(False)
        dialog.skip_btn.setText("Close")
        dialog.exec()

    def _open_legal_policies(self):
        """Opens internal native Legal Policies & EULA dialog."""
        from components.help_dialogs import LegalPoliciesDialog
        dialog = LegalPoliciesDialog(self)
        dialog.exec()

    def _handle_rollback_action(self, prev_version: str, installer_path: str):
        """Allows direct 1-click downgrade to the previous stable release."""
        confirm = QMessageBox.question(
            self,
            "Confirm Rollback",
            f"Are you sure you want to roll back DrawMotion to version v{prev_version}?\n\n"
            "The installer will run immediately and restore your previous version safely.\n"
            "Your projects and user data will not be affected.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            from core.recovery_engine.watchdog import launch_rollback_installer
            launch_rollback_installer(installer_path)
            sys.exit(0)

