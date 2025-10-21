package symbol

import (
	"github.com/spf13/cobra"
)

var Cmd = &cobra.Command{
	Use:   "symbol",
	Short: "Manage and inspect symbols",
	Long:  "View symbol information, profiles, and status",
}
