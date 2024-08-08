import sublime
import sublime_plugin
import re

class ProcessSignalCommandsCommand(sublime_plugin.TextCommand):
    def read_signal_interfaces(self, filepath):
        signal_mappings = {}
        try:
            with open(filepath, 'r') as file:
                for line in file:
                    parts = line.strip().split(',')
                    if len(parts) == 3:
                        signal_name = parts[0].strip().strip('`')
                        set_function = parts[1].strip()
                        get_function = parts[2].strip()
                        signal_mappings[signal_name] = {"set": set_function, "get": get_function}
                        print("parsed")
        except Exception as e:
            sublime.error_message("Error reading signal interfaces file: {}".format(e))
        return signal_mappings

    def run(self, edit):
        filepath = "/home/advo/HIAB/Release/sw/SPACEevo_1.6.0_rc1/firmware/R1.6.0.5/generated/signal_mappings.txt"  # Update this to the actual path

        # Read the signal mappings from the file
        signal_mappings = self.read_signal_interfaces(filepath)

        # Get the entire text of the current file
        entire_text = self.view.substr(sublime.Region(0, self.view.size()))
        lines = entire_text.split("\n")
        new_lines = []
        
        # Compile regex patterns for commands
        set_pattern = re.compile(r'// set value of `(.*)` to (\d+)', re.IGNORECASE)
        get_pattern = re.compile(r'// get value of `(.*)`', re.IGNORECASE)
        check_pattern = re.compile(r'// Check value of `(.*)` == (\d+)', re.IGNORECASE)

        i = 0
        while i < len(lines):
            line = lines[i]

            set_match = set_pattern.match(line)
            get_match = get_pattern.match(line)
            check_match = check_pattern.match(line)

            if set_match:
                
                signal_name = set_match.group(1)
                value = set_match.group(2)

                print("set match name = {}, value = {}".format(signal_name, value))
                if i + 1 <= len(lines) and signal_name in signal_mappings:
                    if i+1 == len(lines):
                        new_lines.append(line)
                        new_lines.append(signal_mappings[signal_name]["set"].replace("val", value) + ";")
                        break
                        
                    next_line = lines[i + 1].strip()
                    if not next_line.startswith(signal_mappings[signal_name]["set"].replace("val", value) + ";"):
                        # Add the command if it's missing
                        print("add the command set")
                        new_lines.append(line)
                        new_lines.append(signal_mappings[signal_name]["set"].replace("val", value) + ";")
                    else:
                        print("Already present command")
                        # The expected command is already present, so just append the comment
                        new_lines.append(line)
                else:
                    print("No following command or signal name not found")
                    new_lines.append(line)
            elif get_match:
                signal_name = get_match.group(1)
                print("get match name = {}".format(signal_name))
                if i + 1 <= len(lines) and signal_name in signal_mappings:
                    if i+1 == len(lines):
                        new_lines.append(line)
                        new_lines.append(signal_mappings[signal_name]["get"] + ";")
                        break

                    next_line = lines[i + 1].strip()
                    if not next_line.startswith(signal_mappings[signal_name]["get"] + ";"):
                        # Add the command if it's missing
                        new_lines.append(line)
                        new_lines.append(signal_mappings[signal_name]["get"] + ";")
                    else:
                        # The expected command is already present, so just append the comment
                        print("Already present command")
                        new_lines.append(line)
                else:
                    # No following command or signal name not found
                    new_lines.append(line)
            elif check_match:
                signal_name = check_match.group(1)
                expected_value = check_match.group(2)
                print("check match name = {}, expected value = {}".format(signal_name, expected_value))
                if i + 1 <= len(lines) and signal_name in signal_mappings:
                    if i+1 == len(lines):
                        new_lines.append(line)
                        new_lines.append('TEST_EQUAL_INT({}, {});'.format(signal_mappings[signal_name]["get"], expected_value))
                        break
                    next_line = lines[i + 1].strip()
                    if not next_line.startswith('TEST_EQUAL_INT({}, {});'.format(signal_mappings[signal_name]["get"], expected_value)):
                        # Add the command if it's missing
                        new_lines.append(line)
                        new_lines.append('TEST_EQUAL_INT({}, {});'.format(signal_mappings[signal_name]["get"], expected_value))
                    else:
                        # The expected command is already present, so just append the comment
                        print("The expected command is already present, so just append the comment")
                        new_lines.append(line)
                else:
                    # No following command or signal name not found
                    print("No following command or signal name not found")
                    new_lines.append(line)
            else:
                new_lines.append(line)

            i += 1

        # Join the modified lines back into a single string
        new_content = "\n".join(new_lines)

        # Replace the entire content of the view with the new content
        region = sublime.Region(0, self.view.size())
        self.view.replace(edit, region, new_content)
