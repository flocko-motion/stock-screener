package error

import (
	"github.com/spf13/cobra"
)

var Cmd = &cobra.Command{
	Use:   "error",
	Short: "Manage system errors",
	Long:  "View, inspect, and clear system errors logged during operations",
}
