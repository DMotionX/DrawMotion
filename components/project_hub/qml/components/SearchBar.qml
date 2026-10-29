import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: searchBar
    height: 44
    color: "transparent"

    RowLayout {
        anchors.fill: parent
        spacing: 12

        // 1. Search Input Box (Clean Vector Magnifying Glass, Zero Emojis)
        Rectangle {
            Layout.preferredWidth: Math.min(320, Math.max(200, searchBar.width * 0.35))
            Layout.fillHeight: true
            color: searchInput.activeFocus ? "#17231D" : "#141A17"
            border.color: searchInput.activeFocus ? "#2E8B57" : "#222C27"
            border.width: searchInput.activeFocus ? 1.5 : 1
            radius: 8
            Behavior on color { ColorAnimation { duration: 150 } }
            Behavior on border.color { ColorAnimation { duration: 150 } }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 10
                spacing: 8

                // Pure Vector Search Icon (No Emoji)
                Canvas {
                    id: searchIconCanvas
                    width: 14
                    height: 14
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.reset();
                        ctx.strokeStyle = searchInput.activeFocus ? "#2E8B57" : "#7E8882";
                        ctx.lineWidth = 1.8;
                        ctx.lineCap = "round";
                        // Circle
                        ctx.beginPath();
                        ctx.arc(5.5, 5.5, 4.2, 0, 2 * Math.PI);
                        ctx.stroke();
                        // Handle
                        ctx.beginPath();
                        ctx.moveTo(8.8, 8.8);
                        ctx.lineTo(12.5, 12.5);
                        ctx.stroke();
                    }
                    Connections {
                        target: searchInput
                        function onActiveFocusChanged() { searchIconCanvas.requestPaint(); }
                    }
                }

                TextField {
                    id: searchInput
                    Layout.fillWidth: true
                    placeholderText: "Search projects by title..."
                    placeholderTextColor: "#6B7280"
                    color: "#FFFFFF"
                    font.family: "Segoe UI"
                    font.pixelSize: 13
                    background: null
                    selectByMouse: true
                    onTextChanged: {
                        if (typeof hubBridge !== "undefined" && hubBridge) {
                            hubBridge.setSearchQuery(text);
                        }
                    }
                }

                // Clear button (Pure Vector Cross, No Emoji)
                Rectangle {
                    visible: searchInput.text.length > 0
                    width: 18
                    height: 18
                    radius: 9
                    color: clearMouse.containsMouse ? "#2A3A31" : "transparent"
                    
                    Canvas {
                        anchors.centerIn: parent
                        width: 10
                        height: 10
                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.reset();
                            ctx.strokeStyle = clearMouse.containsMouse ? "#FFFFFF" : "#9CA3AF";
                            ctx.lineWidth = 1.6;
                            ctx.lineCap = "round";
                            ctx.beginPath();
                            ctx.moveTo(2, 2);
                            ctx.lineTo(8, 8);
                            ctx.moveTo(8, 2);
                            ctx.lineTo(2, 8);
                            ctx.stroke();
                        }
                    }

                    MouseArea {
                        id: clearMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            searchInput.text = ""
                            if (typeof hubBridge !== "undefined" && hubBridge) {
                                hubBridge.setSearchQuery("");
                            }
                        }
                    }
                }
            }
        }

        Item { Layout.fillWidth: true }

        // 2. Project Count
        Text {
            text: (typeof hubBridge !== "undefined" && hubBridge) ? (hubBridge.projectCount + (hubBridge.projectCount === 1 ? " Project" : " Projects")) : ""
            color: "#9CA3AF"
            font.family: "Segoe UI"
            font.pixelSize: 13
            font.bold: true
        }

        // 3. Sort Pill Group (Strictly Bounded, Never Overflowing)
        Rectangle {
            id: sortPillsContainer
            implicitWidth: sortRow.implicitWidth + 8
            implicitHeight: 34
            radius: 8
            color: "#131916"
            border.color: "#222C27"
            border.width: 1

            RowLayout {
                id: sortRow
                anchors.centerIn: parent
                spacing: 2

                Repeater {
                    model: [
                        { label: "Recent", mode: "modified_desc" },
                        { label: "Name", mode: "name_asc" },
                        { label: "Size", mode: "size_desc" }
                    ]

                    Button {
                        id: sortBtn
                        property bool isSelected: (typeof hubBridge !== "undefined" && hubBridge) ? hubBridge.sortMode === modelData.mode : false
                        text: modelData.label
                        onClicked: {
                            if (typeof hubBridge !== "undefined" && hubBridge) {
                                hubBridge.setSortMode(modelData.mode);
                            }
                        }

                        background: Rectangle {
                            color: sortBtn.isSelected ? "#2E8B57" : (sortBtn.hovered ? "#1C2621" : "transparent")
                            radius: 6
                            Behavior on color { ColorAnimation { duration: 120 } }
                        }
                        contentItem: Text {
                            text: sortBtn.text
                            color: sortBtn.isSelected ? "#FFFFFF" : (sortBtn.hovered ? "#E5E7EB" : "#9CA3AF")
                            font.family: "Segoe UI"
                            font.pixelSize: 12
                            font.bold: sortBtn.isSelected
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        padding: 6
                        leftPadding: 12
                        rightPadding: 12
                    }
                }
            }
        }

        // 4. View Mode Switcher (Grid ⊞ vs List ☰ - Pure Vector Icons)
        Rectangle {
            id: viewModeContainer
            implicitWidth: 70
            implicitHeight: 34
            radius: 8
            color: "#131916"
            border.color: "#222C27"
            border.width: 1

            RowLayout {
                anchors.centerIn: parent
                spacing: 2

                // Grid Button
                Button {
                    id: gridBtn
                    property bool isSelected: (typeof hubBridge !== "undefined" && hubBridge) ? hubBridge.viewMode === "grid" : true
                    onClicked: {
                        if (typeof hubBridge !== "undefined" && hubBridge) {
                            hubBridge.setViewMode("grid");
                        }
                    }
                    implicitWidth: 30
                    implicitHeight: 28

                    background: Rectangle {
                        color: gridBtn.isSelected ? "#2E8B57" : (gridBtn.hovered ? "#1C2621" : "transparent")
                        radius: 5
                        Behavior on color { ColorAnimation { duration: 120 } }
                    }
                    contentItem: Canvas {
                        id: gridIconCanvas
                        anchors.centerIn: parent
                        width: 14
                        height: 14
                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.reset();
                            ctx.fillStyle = gridBtn.isSelected ? "#FFFFFF" : (gridBtn.hovered ? "#E5E7EB" : "#9CA3AF");
                            ctx.fillRect(1, 1, 5, 5);
                            ctx.fillRect(8, 1, 5, 5);
                            ctx.fillRect(1, 8, 5, 5);
                            ctx.fillRect(8, 8, 5, 5);
                        }
                        Connections {
                            target: gridBtn
                            function onIsSelectedChanged() { gridIconCanvas.requestPaint(); }
                            function onHoveredChanged() { gridIconCanvas.requestPaint(); }
                        }
                    }
                }

                // List Button
                Button {
                    id: listBtn
                    property bool isSelected: (typeof hubBridge !== "undefined" && hubBridge) ? hubBridge.viewMode === "list" : false
                    onClicked: {
                        if (typeof hubBridge !== "undefined" && hubBridge) {
                            hubBridge.setViewMode("list");
                        }
                    }
                    implicitWidth: 30
                    implicitHeight: 28

                    background: Rectangle {
                        color: listBtn.isSelected ? "#2E8B57" : (listBtn.hovered ? "#1C2621" : "transparent")
                        radius: 5
                        Behavior on color { ColorAnimation { duration: 120 } }
                    }
                    contentItem: Canvas {
                        id: listIconCanvas
                        anchors.centerIn: parent
                        width: 14
                        height: 14
                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.reset();
                            ctx.strokeStyle = listBtn.isSelected ? "#FFFFFF" : (listBtn.hovered ? "#E5E7EB" : "#9CA3AF");
                            ctx.lineWidth = 1.8;
                            ctx.lineCap = "round";
                            ctx.beginPath();
                            ctx.moveTo(2, 3);
                            ctx.lineTo(12, 3);
                            ctx.moveTo(2, 7);
                            ctx.lineTo(12, 7);
                            ctx.moveTo(2, 11);
                            ctx.lineTo(12, 11);
                            ctx.stroke();
                        }
                        Connections {
                            target: listBtn
                            function onIsSelectedChanged() { listIconCanvas.requestPaint(); }
                            function onHoveredChanged() { listIconCanvas.requestPaint(); }
                        }
                    }
                }
            }
        }
    }
}
