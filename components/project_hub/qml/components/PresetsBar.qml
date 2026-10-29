// Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: presetsBar
    height: 50
    color: "#121815"
    border.color: "#1E2923"
    border.width: 1
    radius: 10

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        spacing: 12

        // Section Title with Glowing Accent Dot
        RowLayout {
            spacing: 8

            Rectangle {
                width: 6
                height: 6
                radius: 3
                color: "#2E8B57"
            }

            Text {
                text: "Canvas Presets:"
                color: "#8E9591"
                font.family: "Segoe UI"
                font.pixelSize: 12
                font.bold: true
            }
        }

        // Preset Buttons Row
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Repeater {
                model: [
                    {
                        title: "YouTube / Wide",
                        ratio: "16:9",
                        res: "1920 × 1080",
                        width: 1920,
                        height: 1080,
                        iconW: 20,
                        iconH: 12
                    },
                    {
                        title: "TikTok / Shorts",
                        ratio: "9:16",
                        res: "1080 × 1920",
                        width: 1080,
                        height: 1920,
                        iconW: 12,
                        iconH: 20
                    },
                    {
                        title: "Instagram Post",
                        ratio: "1:1",
                        res: "1080 × 1080",
                        width: 1080,
                        height: 1080,
                        iconW: 15,
                        iconH: 15
                    },
                    {
                        title: "Standard / Slides",
                        ratio: "4:3",
                        res: "1024 × 768",
                        width: 1024,
                        height: 768,
                        iconW: 18,
                        iconH: 14
                    }
                ]

                delegate: Rectangle {
                    id: presetBtn
                    Layout.fillWidth: true
                    Layout.maximumWidth: 220
                    Layout.minimumWidth: 110
                    height: 36
                    radius: 8
                    color: btnMouse.containsMouse ? "#1A2720" : "#161E1A"
                    border.color: btnMouse.containsMouse ? "#2E8B57" : "#243229"
                    border.width: btnMouse.containsMouse ? 1.5 : 1

                    Behavior on color { ColorAnimation { duration: 140 } }
                    Behavior on border.color { ColorAnimation { duration: 140 } }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 8

                        // Vector Aspect Ratio Box Icon (Zero Emojis)
                        Item {
                            width: 22
                            height: 22
                            Rectangle {
                                anchors.centerIn: parent
                                width: modelData.iconW
                                height: modelData.iconH
                                radius: 2
                                color: "transparent"
                                border.color: btnMouse.containsMouse ? "#3FA36D" : "#76827B"
                                border.width: 1.5
                            }
                        }

                        // Preset Title and Aspect Ratio Details
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1

                            Text {
                                text: modelData.title
                                color: btnMouse.containsMouse ? "#FFFFFF" : "#D1D5DB"
                                font.family: "Segoe UI"
                                font.pixelSize: 11
                                font.bold: true
                                elide: Text.ElideRight
                            }

                            Text {
                                text: modelData.ratio + "  •  " + modelData.res
                                color: btnMouse.containsMouse ? "#56C98B" : "#808A83"
                                font.family: "Segoe UI"
                                font.pixelSize: 9
                                elide: Text.ElideRight
                            }
                        }
                    }

                    MouseArea {
                        id: btnMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: hubBridge.createNewProjectWithPreset("", modelData.width, modelData.height)
                    }

                    ToolTip.visible: btnMouse.containsMouse
                    ToolTip.delay: 400
                    ToolTip.text: "Create fresh " + modelData.title + " (" + modelData.res + ") project"
                }
            }
        }
    }
}
