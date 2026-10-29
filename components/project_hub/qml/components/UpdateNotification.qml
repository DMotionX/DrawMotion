import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    visible: (typeof updateBridge !== "undefined" && updateBridge !== null) ? Boolean(updateBridge.hasUpdate) : false
    height: visible ? 54 : 0
    color: "#14261C"
    border.color: "#2E8B57"
    border.width: 1
    radius: 10
    clip: true

    Behavior on height {
        NumberAnimation { duration: 250; easing.type: Easing.OutCubic }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        spacing: 14

        // Sparkle Icon / Badge
        Rectangle {
            width: 30
            height: 30
            radius: 15
            color: "#2E8B57"
            border.color: "#56C98B"
            border.width: 1

            Text {
                anchors.centerIn: parent
                text: "★"
                color: "#FFFFFF"
                font.pixelSize: 14
                font.bold: true
            }
        }

        // Notification Message
        Text {
            text: (typeof updateBridge !== "undefined" && updateBridge !== null) ? ("New Release Available: v" + (updateBridge.latestVersion || "") + "  (Current: v" + (updateBridge.currentVersion || "") + ")") : ""
            color: "#FFFFFF"
            font.family: "Segoe UI"
            font.pixelSize: 13
            font.bold: true
            Layout.fillWidth: true
            elide: Text.ElideRight
        }

        // What's New Button
        Button {
            id: changelogBtn
            text: "What's New"
            onClicked: {
                if (typeof updateBridge !== "undefined" && updateBridge !== null) {
                    updateBridge.openChangelog();
                }
            }
            background: Rectangle {
                color: changelogBtn.hovered ? "#22352A" : "transparent"
                border.color: changelogBtn.hovered ? "#56C98B" : "#3FA36D"
                border.width: 1
                radius: 6
            }
            contentItem: Text {
                text: changelogBtn.text
                color: "#FFFFFF"
                font.family: "Segoe UI"
                font.pixelSize: 12
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            padding: 6
            leftPadding: 12
            rightPadding: 12
        }

        // Update Now Action Button
        Button {
            id: updateBtn
            text: "Update Now"
            onClicked: {
                if (typeof updateBridge !== "undefined" && updateBridge !== null) {
                    updateBridge.triggerUpdate();
                }
            }
            background: Rectangle {
                radius: 6
                gradient: Gradient {
                    GradientStop {
                        position: 0.0
                        color: updateBtn.pressed ? "#1B5534" : (updateBtn.hovered ? "#3FA36D" : "#2E8B57")
                    }
                    GradientStop {
                        position: 1.0
                        color: updateBtn.pressed ? "#16452B" : (updateBtn.hovered ? "#2E8B57" : "#226B42")
                    }
                }
                border.color: updateBtn.hovered ? "#56C98B" : "#389B63"
                border.width: 1
            }
            contentItem: Text {
                text: updateBtn.text
                color: "#FFFFFF"
                font.family: "Segoe UI"
                font.pixelSize: 12
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            padding: 6
            leftPadding: 14
            rightPadding: 14
        }

        // Dismiss Button
        Button {
            id: dismissBtn
            text: "✕"
            onClicked: {
                if (typeof updateBridge !== "undefined" && updateBridge !== null) {
                    updateBridge.dismissUpdate();
                }
            }
            background: Rectangle {
                color: dismissBtn.hovered ? "#263B30" : "transparent"
                radius: 12
            }
            contentItem: Text {
                text: dismissBtn.text
                color: dismissBtn.hovered ? "#FFFFFF" : "#9CA3AF"
                font.pixelSize: 12
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Layout.preferredWidth: 26
            Layout.preferredHeight: 26
        }
    }
}
