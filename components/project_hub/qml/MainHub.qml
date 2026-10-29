import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Rectangle {
    id: windowRoot
    width: 1040
    height: 680
    color: theme.bgMain

    Theme { id: theme }

    // Ambient Top Spotlight Gradient for Studio Depth
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 260
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#16281F" }
            GradientStop { position: 0.6; color: "#0B1510" }
            GradientStop { position: 1.0; color: "#000D110F" }
        }
    }

    // Keyboard Shortcuts
    Shortcut {
        sequence: "Ctrl+N"
        onActivated: {
            if (typeof hubBridge !== "undefined" && hubBridge) {
                hubBridge.createNewProject("");
            }
        }
    }

    Shortcut {
        sequence: "Ctrl+O"
        onActivated: {
            if (typeof hubBridge !== "undefined" && hubBridge) {
                hubBridge.browseProject();
            }
        }
    }

    Shortcut {
        sequence: "Escape"
        onActivated: {
            if (typeof hubBridge !== "undefined" && hubBridge) {
                hubBridge.closeHub();
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        // 1. Dual-Context Update Banner (Only visible when update is found)
        UpdateNotification {
            Layout.fillWidth: true
        }

        // 2. Header Bar (Branding & Global Actions)
        HeaderBar {
            Layout.fillWidth: true
        }

        // 3. Platform Canvas Presets Bar (YouTube 16:9, TikTok 9:16, Instagram 1:1, Classic 4:3)
        PresetsBar {
            Layout.fillWidth: true
        }

        // 4. Search and Sort Filter Bar
        SearchBar {
            Layout.fillWidth: true
        }

        // 4. Main Body: Projects Grid, Projects List, or Empty Welcome State
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ProjectsGrid {
                anchors.fill: parent
                visible: (typeof projectModel !== "undefined" && projectModel) ? (projectModel.count > 0 && ((typeof hubBridge !== "undefined" && hubBridge) ? hubBridge.viewMode === "grid" : true)) : false
            }

            ProjectsList {
                anchors.fill: parent
                visible: (typeof projectModel !== "undefined" && projectModel) ? (projectModel.count > 0 && ((typeof hubBridge !== "undefined" && hubBridge) ? hubBridge.viewMode === "list" : false)) : false
            }

            EmptyState {
                anchors.fill: parent
                visible: (typeof projectModel !== "undefined" && projectModel) ? (projectModel.count === 0) : true
            }
        }

        // 5. Storage Insights & Folder Access Footer
        Rectangle {
            Layout.fillWidth: true
            height: 30
            color: "transparent"

            RowLayout {
                anchors.fill: parent
                spacing: 12

                Text {
                    text: (typeof hubBridge !== "undefined" && hubBridge) ? ("Storage: " + hubBridge.totalStorageFormatted + " across " + hubBridge.projectCount + (hubBridge.projectCount === 1 ? " project" : " projects")) : ""
                    color: "#6B7280"
                    font.family: "Segoe UI"
                    font.pixelSize: 11
                }

                Item { Layout.fillWidth: true }

                Button {
                    id: folderBtn
                    text: "Open Projects Folder ➔"
                    onClicked: {
                        if (typeof hubBridge !== "undefined" && hubBridge) {
                            hubBridge.openProjectsDirectory();
                        }
                    }

                    background: Rectangle {
                        color: folderBtn.hovered ? "#1A2520" : "transparent"
                        border.color: folderBtn.hovered ? "#2E8B57" : "transparent"
                        border.width: 1
                        radius: 4
                        Behavior on color { ColorAnimation { duration: 120 } }
                    }
                    contentItem: Text {
                        text: folderBtn.text
                        color: folderBtn.hovered ? "#3FA36D" : "#8E9591"
                        font.family: "Segoe UI"
                        font.pixelSize: 11
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    padding: 4
                    leftPadding: 8
                    rightPadding: 8
                }
            }
        }
    }
}
