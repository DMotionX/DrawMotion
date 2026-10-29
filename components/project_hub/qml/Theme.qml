import QtQuick

QtObject {
    id: theme

    // Backgrounds & Surfaces
    readonly property color bgMain: "#0D110F"
    readonly property color bgSecondary: "#131916"
    readonly property color panel: "#18201C"
    readonly property color surface: "#1D2722"
    readonly property color surfaceHover: "#23302A"

    // Cards & Borders
    readonly property color cardBg: "#161D19"
    readonly property color cardHover: "#1C2621"
    readonly property color border: "#222C27"
    readonly property color borderHover: "#2E8B57"
    readonly property color borderFocus: "#3FA36D"
    readonly property color divider: "#2A3630"

    // Accents & Gradients
    readonly property color primaryGreen: "#2E8B57"
    readonly property color greenHover: "#3FA36D"
    readonly property color greenPressed: "#20683F"
    readonly property color greenGlow: "#10B981"
    readonly property color dangerRed: "#EF4444"
    readonly property color dangerHover: "#F87171"
    readonly property color purpleAccent: "#8B5CF6"

    // Typography
    readonly property color textPrimary: "#FFFFFF"
    readonly property color textSecondary: "#9CA3AF"
    readonly property color textMuted: "#6B7280"
    readonly property string fontFamily: "Segoe UI"
    
    // Sizing & Spacing
    readonly property int radiusSmall: 6
    readonly property int radiusMedium: 10
    readonly property int radiusLarge: 14
}
