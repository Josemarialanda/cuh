{
  description = "cuh: an esoteric programming language where every statement ends with cuh";

  inputs = {
    nixpkgs.url = "https://channels.nixos.org/nixos-unstable/nixexprs.tar.xz";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system nixpkgs.legacyPackages.${system});
      perSystem = system: pkgs:
      let
        python = pkgs.python313;

        cuh = python.pkgs.buildPythonApplication {
          pname = "cuh";
          version = "0.1.0";
          pyproject = true;
          src = ./.;
          build-system = [ python.pkgs.setuptools ];
          nativeCheckInputs = [ python.pkgs.pytestCheckHook ];
        };
      in
      {
        packages = { default = cuh; inherit cuh; };

        apps.default = {
          type = "app";
          program = "${cuh}/bin/cuh";
        };

        checks.default = cuh;

        devShell = pkgs.mkShell {
          packages = [
            (python.withPackages (ps: [ ps.pytest ]))
          ];
          shellHook = ''
            export PYTHONPATH="$PWD''${PYTHONPATH:+:$PYTHONPATH}"
            alias cuh="python -m cuh"
          '';
        };
      };
      each = forAllSystems perSystem;
    in
    {
      packages = nixpkgs.lib.mapAttrs (_: v: v.packages) each;
      apps = nixpkgs.lib.mapAttrs (_: v: v.apps) each;
      checks = nixpkgs.lib.mapAttrs (_: v: v.checks) each;
      devShells = nixpkgs.lib.mapAttrs (_: v: { default = v.devShell; }) each;
    };
}
