from typing import Dict, List

class PreventionSystem:
    """
    Maps attack classifications to specific prevention controls.
    """
    
    def __init__(self):
        self.mitigations = {
            "Intent-to-act": [
                "Immediate IP Block via Firewall",
                "Terminate Active Sessions",
                "Trigger SIEM Alert (High Severity)",
                "Snapshot System State for Forensics"
            ],
            "Intent-to-probe": [
                "Rate Limit Source IP", 
                "Log Activity for Correlation",
                "Add to Watchlist",
                "Send Fake Responses (Deception)"
            ],
            "SSH Brute Force": [ # Example specific class if we had multi-class
                "Implement Fail2Ban",
                "Disable Password Authentication",
                "Enforce Key-Based Auth"
            ]
        }

    def get_mitigation(self, attack_class: str) -> List[str]:
        """
        Returns a list of mitigation strategies for the given attack class.
        
        Args:
            attack_class (str): The predicted attack class (e.g., 'Intent-to-act').
            
        Returns:
            List[str]: List of recommended actions.
        """
        # Normalize input
        key = str(attack_class)
        
        # In our binary case, we mapped 1 to Intent-to-act and 0 to Intent-to-probe
        if key == "1" or key == "Intent-to-act":
            return self.mitigations["Intent-to-act"]
        elif key == "0" or key == "Intent-to-probe":
            return self.mitigations["Intent-to-probe"]
            
        return self.mitigations.get(key, ["Analyze Log Manually"])

if __name__ == "__main__":
    ps = PreventionSystem()
    print("Mitigation for Intent-to-act:", ps.get_mitigation("Intent-to-act"))
