# reclient-configs

This repository contains configuration script and reclient config extensions to
support Chromium compilation on linux remotes via
[Reclient](https://github.com/bazelbuild/reclient/).

## Usage

```
python3 configure_reclient.py --src_dir=/chromium_checkout/src
```

Help:
```
python3 configure_reclient.py --help
```

## Details

### Configuration steps

1. If a host machine is not linux, download linux clang toolchain and generate
   `clang_remote_wrapper`.
2. Generate reproxy and rewrapper configs.

#### Reproxy config merge

Reproxy config is based on the Chromium config template.
1. Load and substitute
   `//buildtools/reclient_cfgs/reproxy_cfg_templates/reproxy.cfg.template` with
   empty variables.
2. Merge `reproxy.cfg`.

#### Rewrapper configs merge

Rewrapper configs are based on the Chromium linux config.
1. Load `//buildtools/reclient_cfgs/linux/<tool>/rewrapper_linux.cfg`
2. Merge `<tool>/rewrapper_base.cfg`
3. Merge `<tool>/rewrapper_<host_os>.cfg`

#### Remote wrappers

`clang_remote_wrapper` is required to run cross-compilation. It replaces default
clang path with a linux clang path and runs the linux version of the clang
remotely.

### Config merge process

1. Parse a config item and merge it with the existing one or create a new one.
2. If the value is a map, overwrite map items; if it's a list, append
   list items. Map-like and list-like items are hardcoded in
   `ReclientCfg.from_cfg_value()`.
3. If the value is empty, clear the item.

This allows config merger to perform such modifications:

```
# Add/modify/remove items into a map-like value.
# This adds/modifies "OSFamily" and removes "label:action_default".
platform=OSFamily=linux,label:action_default=

# Add items into a list-like value.
inputs=src/new_file,src/new_file2

# Modify a simple value.
canonicalize_working_dir=false

# Fully replace list/map values by clearing it first.
labels=
labels=type=compile,compiler=clang,lang=cpp
platform=
platform=container-image=docker://...
inputs=
inputs=src/a_single_input
```

### Path substitution

Configs may use path placeholders such as `{src_dir}`, `{build_dir}` in some
variables of rewrapper configs. See `ReclientCfg.rebase_if_path_value()` for the
full list of supported variables.

Available placeholders can be found in `Paths` helper declaration. These
placeheolders are substituted and final values are rebased onto
Reclient-expected directory during the config write stage (see
`ReclientCfg.rebase_if_path_value()`).

### Cusomization via external py script

You can pass a custom python script via `--custom_py` that may alter reproxy and
rewrapper configs. The script receives some global objects from the configurator
to make config handling easier (see `ReclientConfigurator.load_custom_py()`). It
may implement some of these functions to be called by the configurator.

```(python)
# Called before the configuration begins.
def pre_configure():
    pass


# Called before writing reproxy.cfg.
def merge_reproxy_cfg(reproxy_cfg):
    reproxy_cfg = ReclientCfg.merge_cfg(
        reproxy_cfg,
        {
            # Increase verbosity for rbe debugging.
            'v': 2,
        })

    return reproxy_cfg


# Called before writing <tool>/rewrapper_<host_os>.cfg.
def merge_rewrapper_cfg(rewrapper_cfg, tool, host_os):
    # Merge with an existing config:
    rewrapper_cfg = ReclientCfg.merge_cfg(
        rewrapper_cfg
        {
            # Do not canonicalize working dir.
            'canonicalize_working_dir': false,
        })

    # Or rewrite it from scratch:
    rewrapper_cfg = {
        'platform' = {
            'container-image': 'docker://gcr.io/...'
            'OSFamily': 'linux',
        }
    }

    return rewrapper_cfg


# Called after the configuration has ended.
def post_configure():
    pass
```
