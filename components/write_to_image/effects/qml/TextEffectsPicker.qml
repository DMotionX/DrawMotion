import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    width: 320
    height: 180
    color: "#18181f"
    radius: 8

    // effectsBridge injected from Python context
    property var bridge: typeof effectsBridge !== "undefined" ? effectsBridge : null

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Text {
            text: "Text Shader Effects"
            color: "#e2e8f0"
            font.pixelSize: 13
            font.bold: true
            Layout.fillWidth: true
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AsNeeded

            Grid {
                id: effectGrid
                width: parent.width
                columns: 2
                columnSpacing: 6
                rowSpacing: 6

                Repeater {
                    model: root.bridge ? root.bridge.getAvailableEffects() : [
                        {"id": "none", "name": "None"},
                        {"id": "glow", "name": "Glow"},
                        {"id": "neon", "name": "Neon"},
                        {"id": "ink_bleed", "name": "Ink Bleed"},
                        {"id": "drop_shadow", "name": "Drop Shadow"},
                        {"id": "glitch", "name": "Glitch"},
                        {"id": "holographic", "name": "Holographic"}
                    ]

                    Rectangle {
                        id: chip
                        // 'None' spans full width across both columns; other effects form a 2-column grid
                        property bool isFullWidth: modelData.id === "none"
                        width: isFullWidth ? effectGrid.width : Math.floor((effectGrid.width - effectGrid.columnSpacing) / 2)
                        height: 32
                        radius: 6

                        property bool isSelected: root.bridge ? (root.bridge.currentEffect === modelData.id) : (modelData.id === "none")
                        property bool isHovered: chipMouse.containsMouse

                        color: isSelected ? "#3b82f6" : (isHovered ? "#2d2d38" : "#22222b")
                        border.color: isSelected ? "#60a5fa" : (isHovered ? "#4a4a58" : "#32323e")
                        border.width: 1

                        Behavior on color { ColorAnimation { duration: 150 } }
                        Behavior on border.color { ColorAnimation { duration: 150 } }

                        Text {
                            anchors.centerIn: parent
                            text: modelData.name
                            color: chip.isSelected ? "#ffffff" : "#cbd5e1"
                            font.pixelSize: 11
                            font.weight: chip.isSelected ? Font.DemiBold : Font.Normal
                        }

                        MouseArea {
                            id: chipMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                if (root.bridge) {
                                    root.bridge.setEffect(modelData.id);
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
